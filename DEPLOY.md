# 部署流程文档

## 流水线概述

```
开发机（当前） → GitHub → 生产机（106.12.165.68） → docker-compose build & up
```

---

## 仓库信息

- **GitHub 仓库**: https://github.com/zhangroc/fund-system
- **生产机**: 106.12.165.68
- **部署目录**: /opt/fund-system

---

## 开发流程

### 1. 开发机 - 提交代码

```bash
cd /home/ubuntu/.openclaw/workspace/fund-system

# 添加并提交代码
git add -A
git commit -m "feat: 描述本次改动"

# 推送到 GitHub
git push origin main
```

### 2. 生产机 - 部署

首次部署：
```bash
# 1. 克隆代码到生产机
git clone https://github.com/zhangroc/fund-system.git /opt/fund-system
cd /opt/fund-system

# 2. 启动服务
docker-compose up -d --build
```

后续更新：
```bash
# SSH 到生产机执行
ssh root@106.12.165.68

# 部署脚本
cd /opt/fund-system
git pull origin main
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## 一键部署脚本（生产机）

创建 `/opt/fund-system/deploy.sh`：

```bash
#!/bin/bash
set -e

echo "=== 开始部署 ==="
cd /opt/fund-system

echo "1. 拉取最新代码..."
git pull origin main

echo "2. 停止旧容器..."
docker-compose down

echo "3. 构建新镜像..."
docker-compose build --no-cache

echo "4. 启动服务..."
docker-compose up -d

echo "=== 部署完成 ==="
docker-compose ps
```

添加执行权限：
```bash
chmod +x /opt/fund-system/deploy.sh
```

后续更新只需：
```bash
ssh root@106.12.165.68 "cd /opt/fund-system && ./deploy.sh"
```

---

## 常用命令

| 操作 | 命令 |
|------|------|
| 查看服务状态 | `docker-compose ps` |
| 查看日志 | `docker-compose logs -f` |
| 重启服务 | `docker-compose restart` |
| 停止服务 | `docker-compose down` |

---

## 注意事项

1. **首次部署前**：确保生产机已安装 Docker + Docker Compose
2. **数据库**：生产机需要初始化 MySQL 数据
3. **前端构建产物**：已被 `frontend/build` 包含在仓库中，后端直接服务静态文件
4. **端口**：确保 80 端口未被占用

---

*文档创建于 2026-03-10*