#!/bin/bash
cd "$(dirname "$0")"

REPO_URL="https://github.com/11195666/Silex.git"
REMOTE_NAME="silex"
BRANCH="master"

echo "========================================="
echo "  Silex 源编译 & 发布工具"
echo "========================================="
echo ""

# Step 1: Confirm compile
read -p "是否编译? (y/n): " yn
if [ "$yn" != "y" ] && [ "$yn" != "Y" ]; then
    echo "已取消。"
    exit 0
fi

echo ""
echo "正在编译..."
rm -rf temp/
rm -f docs/pkg/*.deb
rm -f docs/Packages docs/Packages.bz2 docs/Packages.xz docs/Packages.zst docs/Release
rm -rf docs/depiction/ docs/web/ docs/assets/ docs/api/
rm -f docs/404.html docs/CNAME docs/CydiaIcon.png docs/index.html docs/sileo-featured.json docs/.nojekyll
python3 index.py

if [ $? -ne 0 ]; then
    echo ""
    echo "编译失败，请检查错误信息。"
    exit 1
fi

echo ""
echo "========================================="
echo "  编译完成！"
echo "========================================="
echo ""

# Step 2: Confirm push
read -p "是否发布推送? (y/n): " yn
if [ "$yn" != "y" ] && [ "$yn" != "Y" ]; then
    echo "已取消。编译产物保留在 docs/ 目录，稍后可手动推送。"
    exit 0
fi

echo ""
read -p "请输入 commit 信息: " msg
if [ -z "$msg" ]; then
    echo "commit 信息不能为空，已取消。"
    exit 1
fi

if git remote get-url "$REMOTE_NAME" &>/dev/null; then
    current_url=$(git remote get-url "$REMOTE_NAME")
    if [ "$current_url" != "$REPO_URL" ]; then
        git remote set-url "$REMOTE_NAME" "$REPO_URL"
    fi
else
    git remote add "$REMOTE_NAME" "$REPO_URL"
fi

if [ -d docs/.git ]; then
    echo ""
    echo "检测到 docs/.git 嵌套仓库，正在移除以便将整个 Silex 项目一并提交..."
    rm -rf docs/.git
fi

echo ""
echo "正在提交本地更改..."
git add .
if git diff --cached --quiet; then
    echo "没有需要提交的更改。"
    exit 0
fi
git commit -m "$msg"

echo "正在同步远程仓库..."
git fetch "$REMOTE_NAME" "$BRANCH" 2>/dev/null || true
if git rev-parse "$REMOTE_NAME/$BRANCH" &>/dev/null; then
    if ! git pull --rebase "$REMOTE_NAME" "$BRANCH"; then
        echo ""
        echo "拉取远程更新失败（可能有冲突）。请先手动解决后重试："
        echo "  git pull --rebase $REMOTE_NAME $BRANCH"
        exit 1
    fi
fi

echo "正在推送到 $REPO_URL ..."
git push -u "$REMOTE_NAME" "$BRANCH"

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================="
    echo "  推送成功！"
    echo "========================================="
else
    echo ""
    echo "推送失败，请检查网络或代理设置。"
    exit 1
fi
