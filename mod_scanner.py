"""
Mod Scanner for detecting and analyzing mod files
Handles extraction of mod metadata from JAR files
"""
import os
import json
import zipfile
import logging
import hashlib
from typing import Optional, Dict, Any, List
from datetime import datetime
from mod_manager import ModInfo, ModLoaderType, ModCategory, ModSide

class ModScanner:
    """Handles mod detection and metadata extraction"""
    
    def __init__(self):
        self.supportedformats = ['.jar']
        self.modloaderpatterns = {
            'fabric': ['fabric.mod.json'],
            'forge': ['META-INF/mods.toml', 'mcmod.info'],
            'quilt': ['quilt.mod.json']
        }
    
    def scanmods(self, modsdir: str, forcerescan: bool = False, existingmods: Dict[str, ModInfo] = None) -> Dict[str, ModInfo]:
        """Scan mods directory and detect installed mods"""
        if not modsdir or not os.path.exists(modsdir):
            logging.warning("Mods directory not found or not set")
            return {}
        
        try:
            logging.info("Starting mod scan...")
            
            # Get all .jar files in mods directory
            jarfiles = []
            for root, dirs, files in os.walk(modsdir):
                for file in files:
                    if file.endswith('.jar'):
                        jarfiles.append(os.path.join(root, file))
            
            totalfiles = len(jarfiles)
            if totalfiles == 0:
                return {}
            
            newmods = {}
            updatedmods = []
            
            for i, jarfile in enumerate(jarfiles):
                try:
                    # Get file hash for change detection
                    filehash = self.calculatefilehash(jarfile)
                    
                    # Check if mod already exists and hasn't changed
                    existingmod = None
                    if existingmods:
                        for modinfo in existingmods.values():
                            if modinfo.filepath == jarfile:
                                existingmod = modinfo
                                break
                    
                    if existingmod and existingmod.filehash == filehash and not forcerescan:
                        newmods[existingmod.modid] = existingmod
                        continue
                    
                    # Extract mod information
                    modinfo = self.extractmodinfo(jarfile)
                    if modinfo:
                        if existingmod:
                            # Update existing mod
                            modinfo.installdate = existingmod.installdate
                            modinfo.isfavorite = existingmod.isfavorite
                            modinfo.isessential = existingmod.isessential
                            modinfo.usernotes = existingmod.usernotes
                            modinfo.tags = existingmod.tags
                            updatedmods.append(modinfo.name)
                        
                        newmods[modinfo.modid] = modinfo
                        
                except Exception as e:
                    logging.error(f"Error scanning mod {jarfile}: {e}")
                    continue
            
            logging.info(f"Mod scan completed: {len(newmods)} mods found, {len(updatedmods)} updated")
            return newmods
            
        except Exception as e:
            logging.error(f"Error during mod scan: {e}")
            return {}
    
    def extractmodinfo(self, jarfile: str) -> Optional[ModInfo]:
        """Extract mod information from JAR file"""
        try:
            with zipfile.ZipFile(jarfile, 'r') as zf:
                modinfo = ModInfo(
                    modid="",
                    name="",
                    version="",
                    filename=os.path.basename(jarfile),
                    filepath=jarfile,
                    filesize=os.path.getsize(jarfile),
                    filehash=self.calculatefilehash(jarfile)
                )
                
                # Try different mod metadata formats
                # 1. Try Fabric mod (fabric.mod.json)
                if self.extractfabricinfo(zf, modinfo):
                    modinfo.modloader = ModLoaderType.FABRIC
                    return modinfo
                
                # 2. Try Forge mod (META-INF/mods.toml or mcmod.info)
                if self.extractforgeinfo(zf, modinfo):
                    modinfo.modloader = ModLoaderType.FORGE
                    return modinfo
                
                # 3. Try Quilt mod (quilt.mod.json)
                if self.extractquiltinfo(zf, modinfo):
                    modinfo.modloader = ModLoaderType.QUILT
                    return modinfo
                
                # 4. Fallback to filename parsing
                return self.parsefilenameinfo(modinfo)
                
        except Exception as e:
            logging.error(f"Error extracting mod info from {jarfile}: {e}")
            return None
    
    def extractfabricinfo(self, zipfile: zipfile.ZipFile, modinfo: ModInfo) -> bool:
        """Extract Fabric mod information"""
        try:
            fabricjson = zipfile.read('fabric.mod.json').decode('utf-8')
            fabricdata = json.loads(fabricjson)
            
            modinfo.modid = fabricdata.get('id', '')
            modinfo.name = fabricdata.get('name', '')
            modinfo.version = fabricdata.get('version', '')
            modinfo.description = fabricdata.get('description', '')
            modinfo.website = fabricdata.get('contact', {}).get('homepage', '')
            
            # Authors
            authors = fabricdata.get('authors', [])
            if authors:
                if isinstance(authors[0], dict):
                    modinfo.author = authors[0].get('name', '')
                else:
                    modinfo.author = str(authors[0])
            
            # Dependencies
            depends = fabricdata.get('depends', {})
            modinfo.dependencies = list(depends.keys())
            
            # Environment (side)
            environment = fabricdata.get('environment', '*')
            if environment == 'client':
                modinfo.side = ModSide.CLIENT
            elif environment == 'server':
                modinfo.side = ModSide.SERVER
            else:
                modinfo.side = ModSide.BOTH
            
            return True
            
        except (KeyError, json.JSONDecodeError, UnicodeDecodeError):
            return False
    
    def extractforgeinfo(self, zipfile: zipfile.ZipFile, modinfo: ModInfo) -> bool:
        """Extract Forge mod information"""
        try:
            # Try modern Forge (mods.toml)
            try:
                modstoml = zipfile.read('META-INF/mods.toml').decode('utf-8')
                return self.parseforgetoml(modstoml, modinfo)
            except KeyError:
                pass
            
            # Try legacy Forge (mcmod.info)
            try:
                mcmodjson = zipfile.read('mcmod.info').decode('utf-8')
                return self.parseforgemcmod(mcmodjson, modinfo)
            except KeyError:
                pass
            
            return False
            
        except Exception:
            return False
    
    def parseforgetoml(self, tomlcontent: str, modinfo: ModInfo) -> bool:
        """Parse Forge mods.toml file"""
        try:
            # Simple TOML parsing for mod info
            lines = tomlcontent.split('\n')
            currentmod = {}
            
            for line in lines:
                line = line.strip()
                if line.startswith('modId'):
                    currentmod['modId'] = line.split('=')[1].strip().strip('"')
                elif line.startswith('version'):
                    currentmod['version'] = line.split('=')[1].strip().strip('"')
                elif line.startswith('displayName'):
                    currentmod['displayName'] = line.split('=')[1].strip().strip('"')
                elif line.startswith('description'):
                    currentmod['description'] = line.split('=')[1].strip().strip('"')
                elif line.startswith('authors'):
                    currentmod['authors'] = line.split('=')[1].strip().strip('"')
            
            if currentmod.get('modId'):
                modinfo.modid = currentmod['modId']
                modinfo.name = currentmod.get('displayName', '')
                modinfo.version = currentmod.get('version', '')
                modinfo.description = currentmod.get('description', '')
                modinfo.author = currentmod.get('authors', '')
                return True
            
            return False
            
        except Exception:
            return False
    
    def parseforgemcmod(self, jsoncontent: str, modinfo: ModInfo) -> bool:
        """Parse legacy Forge mcmod.info file"""
        try:
            # Remove BOM if present
            if jsoncontent.startswith('\ufeff'):
                jsoncontent = jsoncontent[1:]
            
            mcmoddata = json.loads(jsoncontent)
            
            if isinstance(mcmoddata, list) and mcmoddata:
                moddata = mcmoddata[0]
            elif isinstance(mcmoddata, dict):
                moddata = mcmoddata
            else:
                return False
            
            modinfo.modid = moddata.get('modid', '')
            modinfo.name = moddata.get('name', '')
            modinfo.version = moddata.get('version', '')
            modinfo.description = moddata.get('description', '')
            modinfo.website = moddata.get('url', '')
            
            # Authors
            authors = moddata.get('authorList', [])
            if authors:
                modinfo.author = ', '.join(authors)
            
            # Dependencies
            dependencies = moddata.get('dependencies', [])
            modinfo.dependencies = dependencies
            
            return True
            
        except (json.JSONDecodeError, KeyError):
            return False
    
    def extractquiltinfo(self, zipfile: zipfile.ZipFile, modinfo: ModInfo) -> bool:
        """Extract Quilt mod information"""
        try:
            quiltjson = zipfile.read('quilt.mod.json').decode('utf-8')
            quiltdata = json.loads(quiltjson)
            
            quiltloader = quiltdata.get('quilt_loader', {})
            metadata = quiltloader.get('metadata', {})
            
            modinfo.modid = quiltloader.get('id', '')
            modinfo.name = metadata.get('name', '')
            modinfo.version = quiltloader.get('version', '')
            modinfo.description = metadata.get('description', '')
            
            # Authors
            contributors = metadata.get('contributors', {})
            if contributors:
                modinfo.author = ', '.join(contributors.keys())
            
            # Dependencies
            depends = quiltloader.get('depends', [])
            modinfo.dependencies = [dep.get('id', '') for dep in depends if isinstance(dep, dict)]
            
            return True
            
        except (KeyError, json.JSONDecodeError, UnicodeDecodeError):
            return False
    
    def parsefilenameinfo(self, modinfo: ModInfo) -> ModInfo:
        """Parse mod information from filename as fallback"""
        filename = os.path.splitext(modinfo.filename)[0]
        
        # Try to extract mod name and version from filename
        # Common patterns: modname-version.jar, modname_version.jar
        parts = filename.replace('_', '-').split('-')
        
        if len(parts) >= 2:
            # Last part might be version
            potential_version = parts[-1]
            if self.islikelyversion(potential_version):
                modinfo.version = potential_version
                modinfo.name = '-'.join(parts[:-1])
            else:
                modinfo.name = filename
                modinfo.version = "unknown"
        else:
            modinfo.name = filename
            modinfo.version = "unknown"
        
        # Generate mod ID from name
        modinfo.modid = modinfo.name.lower().replace(' ', '_').replace('-', '_')
        
        # Set as unknown loader
        modinfo.modloader = ModLoaderType.UNKNOWN
        modinfo.side = ModSide.UNKNOWN
        modinfo.category = ModCategory.OTHER
        
        return modinfo
    
    def islikelyversion(self, text: str) -> bool:
        """Check if text looks like a version string"""
        # Simple heuristic: contains numbers and common version separators
        import re
        version_pattern = r'^[\d]+[\d\.\-\_]*[\d]+$|^[\d]+$'
        return bool(re.match(version_pattern, text))
    
    def calculatefilehash(self, filepath: str) -> str:
        """Calculate file hash for change detection"""
        try:
            hasher = hashlib.sha256()
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception:
            return ""
    
    def detectmodloader(self, jarfile: str) -> ModLoaderType:
        """Detect mod loader type from JAR file"""
        try:
            with zipfile.ZipFile(jarfile, 'r') as zf:
                filelist = zf.namelist()
                
                # Check for Fabric
                if 'fabric.mod.json' in filelist:
                    return ModLoaderType.FABRIC
                
                # Check for Quilt
                if 'quilt.mod.json' in filelist:
                    return ModLoaderType.QUILT
                
                # Check for Forge
                if 'META-INF/mods.toml' in filelist or 'mcmod.info' in filelist:
                    return ModLoaderType.FORGE
                
                # Check for common Forge indicators
                forge_indicators = ['META-INF/MANIFEST.MF']
                for indicator in forge_indicators:
                    if indicator in filelist:
                        try:
                            content = zf.read(indicator).decode('utf-8', errors='ignore')
                            if 'FMLCorePlugin' in content or 'Forge' in content:
                                return ModLoaderType.FORGE
                        except:
                            pass
                
        except Exception as e:
            logging.error(f"Error detecting mod loader for {jarfile}: {e}")
        
        return ModLoaderType.UNKNOWN
    
    def categorizemod(self, modinfo: ModInfo) -> ModCategory:
        """Attempt to categorize mod based on name and description"""
        name_lower = modinfo.name.lower()
        desc_lower = modinfo.description.lower()
        
        # Performance keywords
        performance_keywords = ['optifine', 'fps', 'performance', 'optimization', 'memory', 'lag']
        if any(keyword in name_lower or keyword in desc_lower for keyword in performance_keywords):
            return ModCategory.PERFORMANCE
        
        # Utility keywords
        utility_keywords = ['jei', 'nei', 'waila', 'inventory', 'map', 'minimap', 'utility']
        if any(keyword in name_lower or keyword in desc_lower for keyword in utility_keywords):
            return ModCategory.UTILITY
        
        # Magic keywords
        magic_keywords = ['magic', 'spell', 'wizard', 'mana', 'enchant', 'thaumcraft', 'botania']
        if any(keyword in name_lower or keyword in desc_lower for keyword in magic_keywords):
            return ModCategory.MAGIC
        
        # Tech keywords
        tech_keywords = ['tech', 'machine', 'industrial', 'thermal', 'mekanism', 'enderio']
        if any(keyword in name_lower or keyword in desc_lower for keyword in tech_keywords):
            return ModCategory.TECH
        
        # World gen keywords
        worldgen_keywords = ['biome', 'world', 'generation', 'terrain', 'dimension']
        if any(keyword in name_lower or keyword in desc_lower for keyword in worldgen_keywords):
            return ModCategory.WORLDGEN
        
        # Food keywords
        food_keywords = ['food', 'cooking', 'hunger', 'eat', 'farm', 'harvest']
        if any(keyword in name_lower or keyword in desc_lower for keyword in food_keywords):
            return ModCategory.FOOD
        
        # API/Library keywords
        api_keywords = ['api', 'lib', 'library', 'core', 'base']
        if any(keyword in name_lower for keyword in api_keywords):
            return ModCategory.API
        
        return ModCategory.OTHER
