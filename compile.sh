#\!/bin/bash
cd "$(dirname "$0")"
rm -rf temp/
rm -f docs/pkg/*.deb
rm -f docs/Packages docs/Packages.bz2 docs/Packages.xz docs/Release
rm -rf docs/depiction/ docs/web/ docs/assets/ docs/api/
rm -f docs/404.html docs/CNAME docs/CydiaIcon.png docs/index.html docs/sileo-featured.json
python3 index.py
echo ""
echo "Done. Push:"
echo "  ./ok.sh"
