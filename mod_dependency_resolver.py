"""
Mod Dependency Resolver for Minecraft Server Manager
Handles automatic dependency resolution and installation
"""
import os
import json
import logging
import threading
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import requests
from mod_manager import ModInfo, ModLoaderType

class DependencyType(Enum):
    """Types of dependencies"""
    REQUIRED = "required"
    OPTIONAL = "optional"
    INCOMPATIBLE = "incompatible"
    RECOMMENDED = "recommended"

@dataclass
class DependencyInfo:
    """Dependency information structure"""
    modid: str
    name: str
    version_range: str
    dependency_type: DependencyType
    download_url: str = ""
    project_id: str = ""
    source: str = ""  # curseforge, modrinth, manual
    
    def matches_version(self, version: str) -> bool:
        """Check if version matches the dependency range"""
        # Simple version matching - can be enhanced with proper semver
        if not self.version_range or self.version_range == "*":
            return True
        
        # Handle exact version
        if self.version_range == version:
            return True
        
        # Handle version ranges (basic implementation)
        if ">=" in self.version_range:
            min_version = self.version_range.replace(">=", "").strip()
            return self.compare_versions(version, min_version) >= 0
        
        if ">" in self.version_range:
            min_version = self.version_range.replace(">", "").strip()
            return self.compare_versions(version, min_version) > 0
        
        return False
    
    def compare_versions(self, v1: str, v2: str) -> int:
        """Compare two versions. Returns -1, 0, or 1"""
        # Simple version comparison - can be enhanced
        try:
            def normalize_version(v):
                # Extract numeric parts
                parts = []
                for part in v.split('.'):
                    # Extract numbers from version part
                    num_str = ''.join(c for c in part if c.isdigit())
                    parts.append(int(num_str) if num_str else 0)
                return parts
            
            v1_parts = normalize_version(v1)
            v2_parts = normalize_version(v2)
            
            # Pad shorter version with zeros
            max_len = max(len(v1_parts), len(v2_parts))
            v1_parts.extend([0] * (max_len - len(v1_parts)))
            v2_parts.extend([0] * (max_len - len(v2_parts)))
            
            for a, b in zip(v1_parts, v2_parts):
                if a < b:
                    return -1
                elif a > b:
                    return 1
            
            return 0
            
        except Exception:
            # Fallback to string comparison
            if v1 < v2:
                return -1
            elif v1 > v2:
                return 1
            return 0

class ModDependencyResolver:
    """Advanced dependency resolution system"""
    
    def __init__(self, modmanager, config):
        self.modmanager = modmanager
        self.config = config
        
        # Dependency cache
        self.dependency_cache: Dict[str, List[DependencyInfo]] = {}
        self.resolution_cache: Dict[str, List[str]] = {}
        
        # Well-known dependencies database
        self.known_dependencies = self.load_known_dependencies()
        
        # API clients for external mod sources
        self.api_clients = {}
        
        # Settings
        self.settings = {
            "auto_resolve_dependencies": True,
            "allow_optional_dependencies": False,
            "check_version_compatibility": True,
            "prefer_latest_versions": True,
            "max_resolution_depth": 10,
            "cache_expiry_hours": 24,
            "enable_external_resolution": True
        }
        
        # State
        self.resolution_in_progress = False
        self.resolution_callbacks = []
        
        # Initialize
        self.initialize()
    
    def initialize(self):
        """Initialize the dependency resolver"""
        try:
            self.load_dependency_cache()
            logging.info("ModDependencyResolver initialized")
        except Exception as e:
            logging.error(f"Failed to initialize ModDependencyResolver: {e}")
    
    def load_known_dependencies(self) -> Dict[str, List[DependencyInfo]]:
        """Load database of well-known mod dependencies"""
        known_deps = {
            # Fabric dependencies
            "fabric-api": [],
            "fabric-language-kotlin": [],
            "modmenu": [],
            
            # Forge dependencies
            "forge": [],
            "jei": [],
            "crafttweaker": [],
            
            # Common libraries
            "architectury": [
                DependencyInfo("fabric-api", "Fabric API", "*", DependencyType.REQUIRED),
                DependencyInfo("forge", "Minecraft Forge", "*", DependencyType.REQUIRED)
            ],
            
            # Performance mods
            "optifine": [
                DependencyInfo("optiforge", "OptiForge", "*", DependencyType.OPTIONAL)
            ],
            
            # Popular content mods with known dependencies
            "tinkers-construct": [
                DependencyInfo("mantle", "Mantle", "*", DependencyType.REQUIRED),
                DependencyInfo("forge", "Minecraft Forge", ">=40.0.0", DependencyType.REQUIRED)
            ],
            
            "applied-energistics-2": [
                DependencyInfo("forge", "Minecraft Forge", ">=40.0.0", DependencyType.REQUIRED)
            ],
            
            "botania": [
                DependencyInfo("curios", "Curios API", "*", DependencyType.OPTIONAL),
                DependencyInfo("jei", "Just Enough Items", "*", DependencyType.OPTIONAL)
            ],
            
            "thermal-expansion": [
                DependencyInfo("thermal-foundation", "Thermal Foundation", "*", DependencyType.REQUIRED),
                DependencyInfo("cofh-core", "CoFH Core", "*", DependencyType.REQUIRED)
            ]
        }
        
        return known_deps
    
    def load_dependency_cache(self):
        """Load dependency cache from file"""
        try:
            cache_file = os.path.join(
                self.modmanager.mod_data_dir,  # FIXED: was moddatadir
                "dependency_cache.json"
            )
            
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                # Convert cache data back to DependencyInfo objects
                for modid, deps_data in cache_data.items():
                    deps = []
                    for dep_data in deps_data:
                        dep = DependencyInfo(
                            modid=dep_data['modid'],
                            name=dep_data['name'],
                            version_range=dep_data['version_range'],
                            dependency_type=DependencyType(dep_data['dependency_type']),
                            download_url=dep_data.get('download_url', ''),
                            project_id=dep_data.get('project_id', ''),
                            source=dep_data.get('source', '')
                        )
                        deps.append(dep)
                    self.dependency_cache[modid] = deps
                
                logging.info(f"Loaded dependency cache with {len(self.dependency_cache)} entries")
        
        except Exception as e:
            logging.error(f"Failed to load dependency cache: {e}")
            self.dependency_cache = {}
    
    def save_dependency_cache(self):
        """Save dependency cache to file"""
        try:
            cache_file = os.path.join(
                self.modmanager.mod_data_dir,  # FIXED: was moddatadir
                "dependency_cache.json"
            )
            
            # Convert DependencyInfo objects to serializable dict
            cache_data = {}
            for modid, deps in self.dependency_cache.items():
                deps_data = []
                for dep in deps:
                    dep_data = {
                        'modid': dep.modid,
                        'name': dep.name,
                        'version_range': dep.version_range,
                        'dependency_type': dep.dependency_type.value,
                        'download_url': dep.download_url,
                        'project_id': dep.project_id,
                        'source': dep.source
                    }
                    deps_data.append(dep_data)
                cache_data[modid] = deps_data
            
            os.makedirs(os.path.dirname(cache_file), exist_ok=True)
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            logging.info("Dependency cache saved")
        
        except Exception as e:
            logging.error(f"Failed to save dependency cache: {e}")
    
    def resolve_dependencies(self, modinfo: ModInfo, 
                           install_missing: bool = True) -> Tuple[bool, List[DependencyInfo], List[str]]:
        """Resolve all dependencies for a mod"""
        try:
            self.resolution_in_progress = True
            
            # Get dependencies for the mod
            dependencies = self.get_mod_dependencies(modinfo)
            
            if not dependencies:
                return True, [], []
            
            # Separate by type
            required_deps = [d for d in dependencies if d.dependency_type == DependencyType.REQUIRED]
            optional_deps = [d for d in dependencies if d.dependency_type == DependencyType.OPTIONAL]
            incompatible_deps = [d for d in dependencies if d.dependency_type == DependencyType.INCOMPATIBLE]
            
            # Check for incompatible mods
            conflicts = self.check_incompatible_dependencies(incompatible_deps)
            if conflicts:
                return False, dependencies, conflicts
            
            # Resolve required dependencies
            missing_required = self.find_missing_dependencies(required_deps)
            missing_optional = []
            
            if self.settings["allow_optional_dependencies"]:
                missing_optional = self.find_missing_dependencies(optional_deps)
            
            all_missing = missing_required + missing_optional
            
            # Install missing dependencies if requested
            if install_missing and all_missing:
                success = self.install_missing_dependencies(all_missing)
                if not success:
                    return False, dependencies, ["Failed to install required dependencies"]
            
            # Verify all required dependencies are satisfied
            still_missing = self.find_missing_dependencies(required_deps)
            if still_missing:
                missing_names = [dep.name for dep in still_missing]
                return False, dependencies, [f"Missing required dependencies: {', '.join(missing_names)}"]
            
            return True, dependencies, []
            
        except Exception as e:
            logging.error(f"Error resolving dependencies: {e}")
            return False, [], [f"Dependency resolution failed: {str(e)}"]
        
        finally:
            self.resolution_in_progress = False
    
    def get_mod_dependencies(self, modinfo: ModInfo) -> List[DependencyInfo]:
        """Get dependencies for a specific mod"""
        dependencies = []
        
        # Check cache first
        if modinfo.modid in self.dependency_cache:
            dependencies.extend(self.dependency_cache[modinfo.modid])
        
        # Check known dependencies database
        if modinfo.modid in self.known_dependencies:
            dependencies.extend(self.known_dependencies[modinfo.modid])
        
        # Extract dependencies from mod metadata
        if hasattr(modinfo, 'dependencies') and modinfo.dependencies:
            for dep_id in modinfo.dependencies:
                # Create dependency info if not already present
                if not any(d.modid == dep_id for d in dependencies):
                    dep_info = DependencyInfo(
                        modid=dep_id,
                        name=dep_id,  # Use ID as name if name unknown
                        version_range="*",
                        dependency_type=DependencyType.REQUIRED
                    )
                    dependencies.append(dep_info)
        
        # Check for loader-specific dependencies
        loader_deps = self.get_loader_dependencies(modinfo.modloader)
        dependencies.extend(loader_deps)
        
        return dependencies
    
    def get_loader_dependencies(self, loader: ModLoaderType) -> List[DependencyInfo]:
        """Get dependencies specific to mod loader"""
        loader_deps = []
        
        if loader == ModLoaderType.FABRIC:
            # Fabric mods typically need Fabric API
            loader_deps.append(DependencyInfo(
                modid="fabric-api",
                name="Fabric API",
                version_range="*",
                dependency_type=DependencyType.RECOMMENDED,
                source="modrinth"
            ))
        
        elif loader == ModLoaderType.FORGE:
            # Forge mods need Minecraft Forge (usually bundled)
            pass
        
        elif loader == ModLoaderType.QUILT:
            # Quilt mods might need Quilted Fabric API
            loader_deps.append(DependencyInfo(
                modid="qsl",
                name="Quilt Standard Libraries",
                version_range="*",
                dependency_type=DependencyType.RECOMMENDED,
                source="modrinth"
            ))
        
        return loader_deps
    
    def find_missing_dependencies(self, dependencies: List[DependencyInfo]) -> List[DependencyInfo]:
        """Find dependencies that are not currently installed"""
        missing = []
        
        installed_mods = {}
        if hasattr(self.modmanager, 'installed_mods'):  # FIXED: was installedmods
            installed_mods = self.modmanager.installed_mods
        
        for dep in dependencies:
            # Check if dependency is installed
            if dep.modid not in installed_mods:
                missing.append(dep)
                continue
            
            # Check version compatibility if enabled
            if self.settings["check_version_compatibility"]:
                installed_mod = installed_mods[dep.modid]
                if not dep.matches_version(installed_mod.version):
                    # Version mismatch - might need to update
                    logging.warning(f"Version mismatch for {dep.modid}: "
                                  f"required {dep.version_range}, "
                                  f"installed {installed_mod.version}")
        
        return missing
    
    def check_incompatible_dependencies(self, incompatible_deps: List[DependencyInfo]) -> List[str]:
        """Check for installed mods that are incompatible"""
        conflicts = []
        
        installed_mods = {}
        if hasattr(self.modmanager, 'installed_mods'):  # FIXED: was installedmods
            installed_mods = self.modmanager.installed_mods
        
        for dep in incompatible_deps:
            if dep.modid in installed_mods:
                conflicts.append(f"Incompatible mod installed: {dep.name}")
        
        return conflicts
    
    def install_missing_dependencies(self, missing_deps: List[DependencyInfo]) -> bool:
        """Install missing dependencies"""
        if not self.settings["enable_external_resolution"]:
            logging.info("External dependency resolution disabled")
            return False
        
        success_count = 0
        
        for dep in missing_deps:
            try:
                # Try to download and install dependency
                if self.download_and_install_dependency(dep):
                    success_count += 1
                    logging.info(f"Successfully installed dependency: {dep.name}")
                else:
                    logging.error(f"Failed to install dependency: {dep.name}")
                    
                    # For required dependencies, this is a failure
                    if dep.dependency_type == DependencyType.REQUIRED:
                        return False
            
            except Exception as e:
                logging.error(f"Error installing dependency {dep.name}: {e}")
                if dep.dependency_type == DependencyType.REQUIRED:
                    return False
        
        return success_count > 0 or len(missing_deps) == 0
    
    def download_and_install_dependency(self, dep: DependencyInfo) -> bool:
        """Download and install a single dependency"""
        try:
            # If we have a direct download URL, use it
            if dep.download_url:
                return self.download_from_url(dep)
            
            # Try to resolve from external sources
            if dep.source == "modrinth":
                return self.download_from_modrinth(dep)
            elif dep.source == "curseforge":
                return self.download_from_curseforge(dep)
            else:
                # Try all available sources
                return (self.download_from_modrinth(dep) or 
                       self.download_from_curseforge(dep))
        
        except Exception as e:
            logging.error(f"Error downloading dependency {dep.name}: {e}")
            return False
    
    def download_from_url(self, dep: DependencyInfo) -> bool:
        """Download dependency from direct URL"""
        try:
            import tempfile
            
            response = requests.get(dep.download_url, timeout=30)
            response.raise_for_status()
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.jar', delete=False) as temp_file:
                temp_file.write(response.content)
                temp_path = temp_file.name
            
            # Install using mod manager - FIXED: method name
            success, message = self.modmanager.install_mod(temp_path)
            
            # Clean up temp file
            try:
                os.unlink(temp_path)
            except:
                pass
            
            return success
            
        except Exception as e:
            logging.error(f"Error downloading from URL {dep.download_url}: {e}")
            return False
    
    def download_from_modrinth(self, dep: DependencyInfo) -> bool:
        """Download dependency from Modrinth"""
        try:
            # Search for mod on Modrinth
            search_url = f"https://api.modrinth.com/v2/search"
            params = {
                "query": dep.name,
                "facets": '[["project_type:mod"]]',
                "limit": 1
            }
            
            response = requests.get(search_url, params=params, timeout=10)
            response.raise_for_status()
            
            search_data = response.json()
            
            if not search_data.get("hits"):
                return False
            
            project = search_data["hits"][0]
            project_id = project["project_id"]
            
            # Get project versions
            versions_url = f"https://api.modrinth.com/v2/project/{project_id}/version"
            response = requests.get(versions_url, timeout=10)
            response.raise_for_status()
            
            versions = response.json()
            
            if not versions:
                return False
            
            # Find compatible version
            compatible_version = None
            for version in versions:
                if dep.matches_version(version["version_number"]):
                    compatible_version = version
                    break
            
            if not compatible_version:
                compatible_version = versions[0]  # Use latest
            
            # Download the mod file
            if compatible_version["files"]:
                download_url = compatible_version["files"][0]["url"]
                dep.download_url = download_url
                return self.download_from_url(dep)
            
            return False
            
        except Exception as e:
            logging.error(f"Error downloading from Modrinth: {e}")
            return False
    
    def download_from_curseforge(self, dep: DependencyInfo) -> bool:
        """Download dependency from CurseForge"""
        try:
            # CurseForge API requires API key
            # This is a placeholder - would need actual CurseForge integration
            logging.info(f"CurseForge download not implemented for {dep.name}")
            return False
            
        except Exception as e:
            logging.error(f"Error downloading from CurseForge: {e}")
            return False
    
    def create_dependency_tree(self, modinfo: ModInfo, max_depth: int = 5) -> Dict[str, Any]:
        """Create a dependency tree for visualization"""
        def build_tree(mod_id: str, current_depth: int = 0) -> Dict[str, Any]:
            if current_depth >= max_depth:
                return {"modid": mod_id, "dependencies": [], "max_depth_reached": True}
            
            # Get mod info - FIXED: attribute name
            if hasattr(self.modmanager, 'installed_mods') and mod_id in self.modmanager.installed_mods:
                mod = self.modmanager.installed_mods[mod_id]
                dependencies = self.get_mod_dependencies(mod)
            else:
                dependencies = []
            
            tree_node = {
                "modid": mod_id,
                "installed": mod_id in (self.modmanager.installed_mods if hasattr(self.modmanager, 'installed_mods') else {}),
                "dependencies": []
            }
            
            for dep in dependencies:
                if dep.dependency_type in [DependencyType.REQUIRED, DependencyType.RECOMMENDED]:
                    child_tree = build_tree(dep.modid, current_depth + 1)
                    tree_node["dependencies"].append(child_tree)
            
            return tree_node
        
        return build_tree(modinfo.modid)
    
    def get_dependency_stats(self) -> Dict[str, Any]:
        """Get dependency statistics"""
        stats = {
            "total_cached_dependencies": len(self.dependency_cache),
            "known_dependencies": len(self.known_dependencies),
            "resolution_enabled": self.settings["auto_resolve_dependencies"],
            "external_resolution_enabled": self.settings["enable_external_resolution"]
        }
        
        if hasattr(self.modmanager, 'installed_mods'):  # FIXED: attribute name
            installed_mods = self.modmanager.installed_mods
            
            # Count mods with dependencies
            mods_with_deps = 0
            total_dependencies = 0
            
            for mod in installed_mods.values():
                deps = self.get_mod_dependencies(mod)
                if deps:
                    mods_with_deps += 1
                    total_dependencies += len(deps)
            
            stats.update({
                "mods_with_dependencies": mods_with_deps,
                "total_dependencies": total_dependencies,
                "average_dependencies": total_dependencies / len(installed_mods) if installed_mods else 0
            })
        
        return stats
    
    def validate_mod_compatibility(self, modinfo: ModInfo) -> Tuple[bool, List[str]]:
        """Validate if mod is compatible with current setup"""
        issues = []
        
        # Check loader compatibility
        if hasattr(self.modmanager, 'settings'):
            current_loader = self.modmanager.settings.get('mod_loader_type')  # FIXED: attribute name
            if current_loader and modinfo.modloader.value != current_loader:
                issues.append(f"Mod loader mismatch: mod uses {modinfo.modloader.value}, "
                            f"server uses {current_loader}")
        
        # Check dependencies
        dependencies = self.get_mod_dependencies(modinfo)
        missing_required = [d for d in dependencies 
                          if d.dependency_type == DependencyType.REQUIRED 
                          and d.modid not in (self.modmanager.installed_mods if hasattr(self.modmanager, 'installed_mods') else {})]
        
        if missing_required:
            missing_names = [d.name for d in missing_required]
            issues.append(f"Missing required dependencies: {', '.join(missing_names)}")
        
        # Check for incompatible mods
        incompatible = [d for d in dependencies if d.dependency_type == DependencyType.INCOMPATIBLE]
        conflicts = self.check_incompatible_dependencies(incompatible)
        issues.extend(conflicts)
        
        return len(issues) == 0, issues
    
    def register_resolution_callback(self, callback):
        """Register callback for resolution events"""
        self.resolution_callbacks.append(callback)
    
    def update_dependency_info(self, modid: str, dependencies: List[DependencyInfo]):
        """Update dependency information for a mod"""
        self.dependency_cache[modid] = dependencies
        self.save_dependency_cache()
