#!/bin/bash
#
# @CreationTime
#   2020/07/23 下午2:41:30
# @ModificationDate
#   2020/07/23 下午2:41:30
# @Function
#  发布
# @Usage
#   $ sh ./deploy.sh
#
# @author siu

# 发布项目文档到 6.146
cd ./docs || exit
sshpass -p 'P@ssw0rd2019' scp -r ./*  root@192.168.6.146:/home/test/autotest-docs