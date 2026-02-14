#!/bin/bash

echo "=== 修复 Docker Buildx 版本问题 ==="
echo "当前版本: $(docker buildx version 2>/dev/null | head -1 || echo '未知')"
echo ""

# 选项
echo "请选择修复方案:"
echo "1) 快速修复: 设置 DOCKER_BUILDKIT=0 (推荐先尝试)"
echo "2) 手动升级 Buildx 到 v0.17.0"
echo "3) 升级 Docker 到 24.x 版本"
echo "4) 使用 Docker Compose 插件 (替代 docker-compose)"
read -p "请输入选项 (1-4): " option

case $option in
    1)
        echo "执行方案 1: 设置 DOCKER_BUILDKIT=0"
        echo "export DOCKER_BUILDKIT=0" >> ~/.bashrc
        source ~/.bashrc
        echo "设置完成，请重新运行命令"
        ;;
    2)
        echo "执行方案 2: 手动升级 Buildx"
        
        # 下载 Buildx v0.17.0
        echo "下载 Buildx v0.17.0..."
        curl -L https://github.com/docker/buildx/releases/download/v0.17.0/buildx-v0.17.0.linux-amd64 -o /tmp/docker-buildx
        
        # 安装到 Docker 插件目录
        echo "安装 Buildx..."
        sudo mkdir -p /usr/libexec/docker/cli-plugins
        sudo cp /tmp/docker-buildx /usr/libexec/docker/cli-plugins/docker-buildx
        sudo chmod +x /usr/libexec/docker/cli-plugins/docker-buildx
        
        # 验证
        echo "验证版本:"
        docker buildx version
        ;;
    3)
        echo "执行方案 3: 升级 Docker"
        
        # 卸载旧版本
        echo "卸载旧版本 Docker..."
        sudo yum remove -y docker-ce docker-ce-cli containerd.io
        
        # 安装 Docker 24.x
        echo "安装 Docker 24.x..."
        sudo yum install -y yum-utils
        sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
        sudo yum install -y docker-ce-24.0.6 docker-ce-cli-24.0.6 containerd.io
        
        # 启动 Docker
        sudo systemctl start docker
        sudo systemctl enable docker
        
        echo "安装完成，请验证版本"
        ;;
    4)
        echo "执行方案 4: 使用 Docker Compose 插件"
        
        # 安装 docker-compose-plugin
        sudo yum install -y docker-compose-plugin
        
        echo "安装完成，请使用 'docker compose' 命令代替 'docker-compose'"
        echo "例如: docker compose -f docker-compose.api.yml up --build -d"
        ;;
    *)
        echo "无效选项"
        exit 1
        ;;
esac

echo ""
echo "修复完成！"