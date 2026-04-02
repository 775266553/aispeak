from bilibili_api import user, Credential
import asyncio
import json

SESSDATA = "2a10e5f1%2C1788143404%2Ca06ca%2A32CjBtOOE7zXQPMvxfMGlwCX_vhqGkydiZ1kVS_Odcvz5EVr8_WoN-gmvrha_d9WMtG1MSVmZaOVVGdzVnQ3l1amNScFJXU2FERkgwRzFuTGdnTU9Xancwakt0eHp0TkxZUzhLZjFzanZ4ang3d2pSWU1kd1NteU0tRzZTdVllX3ZfRkpwdG1yRDBRIIEC"
BILI_JCT = "1adb2b2b8db4b697bc7e764e8e13e5a9"
BUVID3 = "5CE862AE-84A4-65DB-EADE-5C3965BC87BE33376infoc"

async def debug_user_info():
    credential = Credential(sessdata=SESSDATA, bili_jct=BILI_JCT, buvid3=BUVID3)
    u = user.User(uid=1140672573, credential=credential)

    print(f"获取用户信息...")
    user_info = await u.get_user_info()
    print(json.dumps(user_info, ensure_ascii=False, indent=2)[:2000])

if __name__ == "__main__":
    asyncio.run(debug_user_info())
