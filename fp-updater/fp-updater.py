from aiohttp import ClientSession
from aiopath import AsyncPath
from PIL import Image
from tempfile import NamedTemporaryFile

import asyncio
import argparse
import random
import shutil

REPOS = ('https://repo.chariz.com', 'https://havoc.app')


def convert_img(package: dict, fp: bytes, path: AsyncPath) -> None:
    with NamedTemporaryFile('rb+') as tmpfile:
        tmpfile.write(fp)
        tmpfile.flush()

        img = Image.open(tmpfile.name)

    if path.suffix == '.jpg':  # Resize banners to 1280x720
        img = img.resize((1280, 720), Image.ANTIALIAS)
    elif path.suffix == '.png':  # Resize icons to 250x250
        img = img.resize((250, 250), Image.ANTIALIAS)

    if img.mode != 'RGB' and path.suffix == '.jpg':
        img = img.convert('RGB')

    img.save(path, optimize=True)


async def dl_assets(session: ClientSession, package: dict, path: AsyncPath) -> bool:
    icon = await session.get(package['Icon'])
    if icon.status != 200:
        return False

    depiction = await (await session.get(package['SileoDepiction'])).json()
    if 'headerImage' not in depiction.keys():
        return False

    banner = await session.get(depiction['headerImage'])
    if banner.status != 200:
        return False

    await asyncio.to_thread(convert_img, package, await icon.read(), path / 'icon.png')
    await asyncio.to_thread(
        convert_img, package, await banner.read(), path / 'banner.jpg'
    )

    return True


async def main() -> None:
    parser = argparse.ArgumentParser(
        description='Sileo Featured Page Updater',
        usage='fp-updater.py [options]',
    )
    parser.add_argument(
        '-r',
        '--random',
        help='Choose random packages to update Featured Page with',
        action='store_true',
        default=False,
    )

    args = parser.parse_args()

    if await AsyncPath('Packages').exists():
        await asyncio.to_thread(shutil.rmtree, 'Packages')

    async with ClientSession() as session:
        for repo in REPOS:
            repo_data = await session.get(f'{repo}/Packages')
            if repo_data.status == 404:
                print(f'{repo} does not have a decompressed Packages file, skipping.')
                continue  # TODO: Parse bzip2 compressed package file

            packages = list()
            for p in (await repo_data.text()).split('\n\n'):
                p_dict = dict()
                for l in p.splitlines():
                    if (': ' not in l) or (
                        'Description: ' in l
                    ):  # We don't need the description
                        continue

                    p_dict[l.split(': ')[0]] = l.split(': ')[1]

                if len(p_dict) == 0:
                    continue

                if any(
                    _ == p_dict['Section']
                    for _ in ('Terminal Support', 'System', 'Development')
                ):
                    continue

                packages.append(p_dict)

        filtered_packages = list()  # Remove duplicates
        for p in packages:
            if not any(p['Package'] == _['Package'] for _ in filtered_packages):
                filtered_packages.append(p)

        if args.random:
            featured_packages = list()
            for _ in range(14):
                package = filtered_packages[
                    random.randint(0, len(filtered_packages) - 1)
                ]
                if 'Icon' not in package.keys():
                    continue

                featured_packages.append(package)

            for package in list(featured_packages):
                path = AsyncPath(f"Packages/{package['Name'].replace(' ', '-')}")
                await path.mkdir(parents=True, exist_ok=True)

                if await dl_assets(session, package, path) == False:
                    print(f"Note: Failed to get assets for package: {package['Name']}")
                    featured_packages.pop(featured_packages.index(package))

            print(
                f"Featured packages are: {', '.join([_['Name'] for _ in featured_packages])}"
            )


if __name__ == '__main__':
    asyncio.run(main())
