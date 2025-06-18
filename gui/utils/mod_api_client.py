# gui/utils/modapiclient.py
"""API client for mod repositories (CurseForge, Modrinth)"""
import requests
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import threading
import time

class ModAPIClient:
    """Client for accessing mod repository APIs"""
    
    def __init__(self):
        # API endpoints
        self.curseforge_base = "https://api.curseforge.com/v1"
        self.modrinth_base = "https://api.modrinth.com/v2"
        
        # API keys (would be configured by user)
        self.curseforge_key = None  # User needs to provide
        self.modrinth_key = None    # Optional for Modrinth
        
        # Cache
        self.cache = {}
        self.cache_timeout = timedelta(hours=1)
        
        # Rate limiting
        self.last_request = {}
        self.min_interval = 0.1  # 100ms between requests
    
    def set_api_keys(self, curseforge_key: str = None, modrinth_key: str = None):
        """Set API keys for services"""
        self.curseforge_key = curseforge_key
        self.modrinth_key = modrinth_key
    
    def search_mods(self, query: str, game_version: str = None, mod_loader: str = None, 
                   source: str = "both", limit: int = 20) -> Dict[str, List[Dict]]:
        """Search for mods across repositories"""
        results = {"curseforge": [], "modrinth": []}
        
        if source in ["both", "curseforge"] and self.curseforge_key:
            try:
                cf_results = self.search_curseforge(query, game_version, mod_loader, limit)
                results["curseforge"] = cf_results
            except Exception as e:
                logging.error(f"CurseForge search error: {e}")
        
        if source in ["both", "modrinth"]:
            try:
                mr_results = self.search_modrinth(query, game_version, mod_loader, limit)
                results["modrinth"] = mr_results
            except Exception as e:
                logging.error(f"Modrinth search error: {e}")
        
        return results
    
    def search_curseforge(self, query: str, game_version: str = None, 
                         mod_loader: str = None, limit: int = 20) -> List[Dict]:
        """Search CurseForge for mods"""
        if not self.curseforge_key:
            return []
        
        cache_key = f"cf_search_{query}_{game_version}_{mod_loader}_{limit}"
        cached = self.get_cached(cache_key)
        if cached:
            return cached
        
        headers = {
            "x-api-key": self.curseforge_key,
            "Accept": "application/json"
        }
        
        params = {
            "gameId": 432,  # Minecraft
            "searchFilter": query,
            "sortField": 2,  # Popularity
            "sortOrder": "desc",
            "pageSize": limit,
            "index": 0
        }
        
        if game_version:
            params["gameVersion"] = game_version
        if mod_loader:
            params["modLoaderType"] = self.get_curseforge_loader_id(mod_loader)
        
        try:
            self.rate_limit("curseforge")
            response = requests.get(
                f"{self.curseforge_base}/mods/search",
                headers=headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            mods = []
            
            for mod in data.get("data", []):
                mod_info = {
                    "id": str(mod["id"]),
                    "name": mod["name"],
                    "summary": mod["summary"],
                    "authors": [author["name"] for author in mod.get("authors", [])],
                    "download_count": mod.get("downloadCount", 0),
                    "logo": mod.get("logo", {}).get("url"),
                    "game_versions": [v["gameVersion"] for v in mod.get("latestFilesIndexes", [])],
                    "categories": [cat["name"] for cat in mod.get("categories", [])],
                    "last_updated": mod.get("dateModified"),
                    "project_url": mod.get("links", {}).get("websiteUrl"),
                    "source": "curseforge"
                }
                mods.append(mod_info)
            
            self.cache_result(cache_key, mods)
            return mods
            
        except Exception as e:
            logging.error(f"CurseForge API error: {e}")
            return []
    
    def search_modrinth(self, query: str, game_version: str = None, 
                       mod_loader: str = None, limit: int = 20) -> List[Dict]:
        """Search Modrinth for mods"""
        cache_key = f"mr_search_{query}_{game_version}_{mod_loader}_{limit}"
        cached = self.get_cached(cache_key)
        if cached:
            return cached
        
        headers = {"Accept": "application/json"}
        if self.modrinth_key:
            headers["Authorization"] = self.modrinth_key
        
        # Build facets for filtering
        facets = [["project_type:mod"]]
        if game_version:
            facets.append([f"versions:{game_version}"])
        if mod_loader:
            facets.append([f"categories:{mod_loader.lower()}"])
        
        params = {
            "query": query,
            "facets": json.dumps(facets),
            "limit": limit,
            "offset": 0,
            "index": "relevance"
        }
        
        try:
            self.rate_limit("modrinth")
            response = requests.get(
                f"{self.modrinth_base}/search",
                headers=headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            mods = []
            
            for mod in data.get("hits", []):
                mod_info = {
                    "id": mod["project_id"],
                    "name": mod["title"],
                    "summary": mod["description"],
                    "authors": [mod["author"]],
                    "download_count": mod.get("downloads", 0),
                    "logo": mod.get("icon_url"),
                    "game_versions": mod.get("versions", []),
                    "categories": mod.get("categories", []),
                    "last_updated": mod.get("date_modified"),
                    "project_url": f"https://modrinth.com/mod/{mod['slug']}",
                    "source": "modrinth"
                }
                mods.append(mod_info)
            
            self.cache_result(cache_key, mods)
            return mods
            
        except Exception as e:
            logging.error(f"Modrinth API error: {e}")
            return []
    
    def get_mod_versions(self, project_id: str, source: str) -> List[Dict]:
        """Get available versions for a mod"""
        if source == "curseforge":
            return self.get_curseforge_versions(project_id)
        elif source == "modrinth":
            return self.get_modrinth_versions(project_id)
        return []
    
    def get_curseforge_versions(self, mod_id: str) -> List[Dict]:
        """Get CurseForge mod versions"""
        if not self.curseforge_key:
            return []
        
        cache_key = f"cf_versions_{mod_id}"
        cached = self.get_cached(cache_key)
        if cached:
            return cached
        
        headers = {
            "x-api-key": self.curseforge_key,
            "Accept": "application/json"
        }
        
        try:
            self.rate_limit("curseforge")
            response = requests.get(
                f"{self.curseforge_base}/mods/{mod_id}/files",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            versions = []
            
            for file in data.get("data", []):
                version_info = {
                    "id": str(file["id"]),
                    "name": file["fileName"],
                    "version": file.get("displayName", file["fileName"]),
                    "download_url": file.get("downloadUrl"),
                    "file_size": file.get("fileLength", 0),
                    "upload_date": file.get("fileDate"),
                    "game_versions": [v["gameVersion"] for v in file.get("gameVersions", [])],
                    "release_type": file.get("releaseType", 1),  # 1=release, 2=beta, 3=alpha
                    "dependencies": file.get("dependencies", [])
                }
                versions.append(version_info)
            
            self.cache_result(cache_key, versions)
            return versions
            
        except Exception as e:
            logging.error(f"CurseForge versions API error: {e}")
            return []
    
    def get_modrinth_versions(self, project_id: str) -> List[Dict]:
        """Get Modrinth mod versions"""
        cache_key = f"mr_versions_{project_id}"
        cached = self.get_cached(cache_key)
        if cached:
            return cached
        
        headers = {"Accept": "application/json"}
        if self.modrinth_key:
            headers["Authorization"] = self.modrinth_key
        
        try:
            self.rate_limit("modrinth")
            response = requests.get(
                f"{self.modrinth_base}/project/{project_id}/version",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            versions = []
            
            for version in data:
                primary_file = version.get("files", [{}])[0]
                
                version_info = {
                    "id": version["id"],
                    "name": version["name"],
                    "version": version["version_number"],
                    "download_url": primary_file.get("url"),
                    "file_size": primary_file.get("size", 0),
                    "upload_date": version.get("date_published"),
                    "game_versions": version.get("game_versions", []),
                    "release_type": version.get("version_type", "release"),
                    "dependencies": version.get("dependencies", [])
                }
                versions.append(version_info)
            
            self.cache_result(cache_key, versions)
            return versions
            
        except Exception as e:
            logging.error(f"Modrinth versions API error: {e}")
            return []
    
    def download_mod(self, download_url: str, filename: str, 
                    progress_callback: callable = None) -> bool:
        """Download a mod file"""
        try:
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback and total_size > 0:
                            progress = (downloaded / total_size) * 100
                            progress_callback(progress)
            
            return True
            
        except Exception as e:
            logging.error(f"Download error: {e}")
            return False
    
    def rate_limit(self, service: str):
        """Simple rate limiting"""
        now = time.time()
        last = self.last_request.get(service, 0)
        elapsed = now - last
        
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        
        self.last_request[service] = time.time()
    
    def get_cached(self, key: str) -> Optional[Any]:
        """Get cached result if still valid"""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if datetime.now() - timestamp < self.cache_timeout:
                return data
            else:
                del self.cache[key]
        return None
    
    def cache_result(self, key: str, data: Any):
        """Cache a result"""
        self.cache[key] = (data, datetime.now())
    
    def get_curseforge_loader_id(self, loader: str) -> int:
        """Get CurseForge loader type ID"""
        loader_map = {
            "forge": 1,
            "fabric": 4,
            "quilt": 5
        }
        return loader_map.get(loader.lower(), 1)
