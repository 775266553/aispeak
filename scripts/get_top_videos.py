from bilibili_api import user, Credential
import asyncio
import json

SESSDATA = "2a10e5f1%2C1788143404%2Ca06ca%2A32CjBtOOE7zXQPMvxfMGlwCX_vhqGkydiZ1kVS_Odcvz5EVr8_WoN-gmvrha_d9WMtG1MSVmZaOVVGdzVnQ3l1amNScFJXU2FERkgwRzFuTGdnTU9Xancwakt0eHp0TkxZUzhLZjFzanZ4ang3d2pSWU1kd1NteU0tRzZTdVllX3ZfRkpwdG1yRDBRIIEC"
BILI_JCT = "1adb2b2b8db4b697bc7e764e8e13e5a9"
BUVID3 = "5CE862AE-84A4-65DB-EADE-5C3965BC87BE33376infoc"

async def get_top_videos(uid, top_n=10):
    credential = Credential(sessdata=SESSDATA, bili_jct=BILI_JCT, buvid3=BUVID3)
    u = user.User(uid=uid, credential=credential)

    print(f"获取用户信息...")
    user_info = await u.get_user_info()
    print(f"UP主: {user_info['name']}")

    print(f"获取视频列表...")
    videos = []
    pn = 1
    while len(videos) < top_n * 2:
        await asyncio.sleep(0.5)
        page = await u.get_videos(pn=pn, ps=30)
        print(f"第{pn}页，返回数量: {len(page.get('list', []))}")

        if not page.get('list'):
            break

        for v in page['list']:
            if isinstance(v, dict):
                stat = v.get('stat', {}) if isinstance(v.get('stat'), dict) else {}
                videos.append({
                    'bvid': v.get('bvid', ''),
                    'title': v.get('title', ''),
                    'aid': v.get('aid', 0),
                    'view': stat.get('view', 0) if isinstance(stat, dict) else 0,
                    'like': stat.get('like', 0) if isinstance(stat, dict) else 0,
                    'duration': v.get('duration', 0)
                })

        if len(page['list']) < 30:
            break
        pn += 1

    if not videos:
        print("没有获取到视频数据")
        return []

    videos_sorted = sorted(videos, key=lambda x: x['view'], reverse=True)

    print(f"\n播放量 Top {top_n}:")
    print("-" * 80)
    for i, v in enumerate(videos_sorted[:top_n], 1):
        mins = v['duration'] // 60
        secs = v['duration'] % 60
        print(f"{i:2}. {v['title'][:40]}")
        print(f"    BV: {v['bvid']} | 播放: {v['view']:,} | 时长: {mins}:{secs:02d}")

    with open('top10_videos.json', 'w', encoding='utf-8') as f:
        json.dump(videos_sorted[:top_n], f, ensure_ascii=False, indent=2)

    return videos_sorted[:top_n]

if __name__ == "__main__":
    asyncio.run(get_top_videos(1140672573, 10))
