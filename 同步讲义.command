#!/bin/zsh
cd -- "${0:A:h}"
python3 scripts/sync_mechanics.py --publish
result=$?
if [ "$result" -ne 0 ]; then
  echo "同步未完成，请查看上面的提示。"
fi
echo "按回车键关闭窗口。"
read -r
exit "$result"
