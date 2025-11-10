# api/ff_client.py

import requests
import json
from datetime import datetime
from utils import EnC_AEs, DeCode_PackEt, EnC_Uid, ToKen_GeneRaTe
import logging

class FreeFireClient:
    def __init__(self, user_id, password):
        self.user_id = user_id
        self.password = password
        self.jwt_token = None
        self.debug_payload = None # لتخزين الـ payload للتحقق

    def get_payload_debug_info(self):
        """تُرجع جزءاً من الـ payload للتحقق من أنه محدث."""
        _, raw_payload = ToKen_GeneRaTe("debug_token", "debug_uid")
        return raw_payload.hex()[0:30] # طباعة أول 30 حرفاً فقط

    def is_authenticated(self):
        return self.jwt_token is not None

    def authenticate(self):
        url = "https://100067.connect.garena.com/oauth/guest/token/grant"
        data = {
            "uid": self.user_id, "password": self.password, "response_type": "token",
            "client_type": "2", "client_id": "100067",
            "client_secret": "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"
        }
        response = requests.post(url, data=data, verify=False, timeout=20)
        response.raise_for_status()
        
        token_data = response.json()
        access_token = token_data['access_token']
        open_id = token_data['open_id']

        payload, _ = ToKen_GeneRaTe(access_token, open_id)
        
        jwt_url = "https://loginbp.ggwhitehawk.com/MajorLogin"
        headers = {
            'X-Unity-Version': '2018.4.11f1', 'ReleaseVersion': 'OB51', 
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 9; G011A Build/PI)'
        }
        jwt_response = requests.post(jwt_url, headers=headers, data=payload, verify=False, timeout=20)
        jwt_response.raise_for_status()

        try:
            decoded_jwt_data = json.loads(DeCode_PackEt(jwt_response.content.hex()))
            if '8' in decoded_jwt_data and 'data' in decoded_jwt_data['8']:
                self.jwt_token = decoded_jwt_data['8']['data']
                return True
            else:
                raise KeyError(f"JWT token key '8' not found in response. Response data: {decoded_jwt_data}")
        except (json.JSONDecodeError, KeyError) as e:
            logging.error(f"Failed to decode or parse JWT response: {e}")
            raise e

    def get_player_info(self, player_uid):
        if not self.is_authenticated():
            raise Exception("Client is not authenticated. Call authenticate() first.")

        url = "https://clientbp.common.ggbluefox.com/GetPlayerPersonalShow"
        headers = {
            'Authorization': f'Bearer {self.jwt_token}',
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Unity-Version': '2018.4.11f1'
        }
        hex_payload = f"08{EnC_Uid(player_uid)}1007"
        encrypted_payload = bytes.fromhex(EnC_AEs(hex_payload))
        
        response = requests.post(url, headers=headers, data=encrypted_payload, verify=False, timeout=20)

        if response.status_code != 200:
            return {"error": "Failed to fetch data from game server", "status_code": response.status_code}

        try:
            hex_response = response.content.hex()
            data = json.loads(DeCode_PackEt(hex_response))
            
            info = data.get("1", {}).get("data", {})
            guild_info = data.get("6", {}).get("data", {})
            guild_leader_info = data.get("7", {}).get("data", {})
            social_info = data.get("9", {}).get("data", {})

            creation_timestamp = info.get("44", {}).get("data")
            last_login_timestamp = info.get("24", {}).get("data")

            return {
                "uid": info.get("1", {}).get("data"),
                "nickname": info.get("3", {}).get("data"),
                "level": info.get("6", {}).get("data"),
                "exp": info.get("7", {}).get("data"),
                "likes": info.get("21", {}).get("data"),
                "region": info.get("5", {}).get("data"),
                "bio": social_info.get("9", {}).get("data", "No Bio"),
                "creation_date": datetime.fromtimestamp(creation_timestamp).isoformat() if creation_timestamp else None,
                "last_login": datetime.fromtimestamp(last_login_timestamp).isoformat() if last_login_timestamp else None,
                "guild": {
                    "id": guild_info.get("1", {}).get("data"),
                    "name": guild_info.get("2", {}).get("data"),
                    "level": guild_info.get("4", {}).get("data"),
                    "member_count": guild_info.get("6", {}).get("data"),
                    "leader_uid": guild_info.get("3", {}).get("data"),
                    "leader_name": guild_leader_info.get("3", {}).get("data")
                } if guild_info else "No Guild"
            }
        except Exception as e:
            return {"error": "Player not found or data parsing failed", "details": str(e)}
