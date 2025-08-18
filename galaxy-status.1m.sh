#!/bin/bash

# <xbar.title>Galaxy System Monitor</xbar.title>
# <xbar.version>v1.0</xbar.version>
# <xbar.author>Galaxy DevOps</xbar.author>
# <xbar.author.github>galaxydev</xbar.author.github>
# <xbar.desc>Monitor Galaxy Developer System services</xbar.desc>
# <xbar.dependencies>bash,nc,curl</xbar.dependencies>

# Refresh every 1 minute - filename: galaxy-status.1m.sh

check_port() {
    nc -z localhost "$1" 2>/dev/null
    return $?
}

# Count running services
RUNNING=0
TOTAL=10

# Check each service
check_port 5432 && ((RUNNING++))  # PostgreSQL
check_port 6379 && ((RUNNING++))  # Redis
check_port 37778 && ((RUNNING++)) # Memory API
check_port 37777 && ((RUNNING++)) # Backend API
check_port 5556 && ((RUNNING++))  # Experience API
check_port 5555 && ((RUNNING++))  # Voice Storage
check_port 8766 && ((RUNNING++))  # DEV Monitor HTTP
check_port 8765 && ((RUNNING++))  # DEV Monitor WS
check_port 8080 && ((RUNNING++))  # DOC System
check_port 8000 && ((RUNNING++))  # Standards Dashboard

# Menu bar display
if [ $RUNNING -eq $TOTAL ]; then
    echo "🟢 Galaxy [$RUNNING/$TOTAL]"
    echo "---"
    echo "✅ All Services Running | color=green"
elif [ $RUNNING -ge 8 ]; then
    echo "🟡 Galaxy [$RUNNING/$TOTAL]"
    echo "---"
    echo "⚠️ Some Services Down | color=orange"
else
    echo "🔴 Galaxy [$RUNNING/$TOTAL]"
    echo "---"
    echo "❌ Critical Issues | color=red"
fi

echo "---"
echo "📊 Service Status"

# Individual service checks with links
echo "---"
if check_port 5432; then
    echo "✅ PostgreSQL (5432) | color=green"
else
    echo "❌ PostgreSQL (5432) | color=red"
fi

if check_port 6379; then
    echo "✅ Redis (6379) | color=green"
else
    echo "❌ Redis (6379) | color=red"
fi

if check_port 37777; then
    echo "✅ Backend API | href=http://localhost:37777 color=green"
else
    echo "❌ Backend API | color=red"
fi

if check_port 37778; then
    echo "✅ Memory API | href=http://localhost:37778/health color=green"
else
    echo "❌ Memory API | color=red"
fi

if check_port 5556; then
    echo "✅ Experience API | href=http://localhost:5556/api/health color=green"
else
    echo "❌ Experience API | color=red"
fi

if check_port 5555; then
    echo "✅ Voice Storage | href=http://localhost:5555 color=green"
else
    echo "❌ Voice Storage | color=red"
fi

if check_port 8766; then
    echo "✅ DEV Monitor | href=http://localhost:8766 color=green"
else
    echo "❌ DEV Monitor | color=red"
fi

if check_port 8080; then
    echo "✅ DOC System | href=http://localhost:8080/api/status color=green"
else
    echo "❌ DOC System | color=red"
fi

if check_port 8000; then
    echo "✅ Standards Dashboard | href=http://localhost:8000 color=green"
else
    echo "❌ Standards Dashboard | color=red"
fi

if check_port 3000; then
    echo "✅ Frontend | href=http://localhost:3000 color=green"
else
    echo "❌ Frontend | color=red"
fi

echo "---"
echo "🎮 Quick Actions"
echo "---"
echo "🚀 Start All Services | bash='/Volumes/Z7S/development/GalaxyDevelopers/DEVELOPER_SYSTEM/GALAXY_ORCHESTRATOR/galaxy-master-simple.sh' param1=start terminal=false refresh=true"
echo "🛑 Stop All Services | bash='/Volumes/Z7S/development/GalaxyDevelopers/DEVELOPER_SYSTEM/GALAXY_ORCHESTRATOR/galaxy-master-simple.sh' param1=stop terminal=false refresh=true"
echo "📊 View Full Status | bash='/Volumes/Z7S/development/GalaxyDevelopers/DEVELOPER_SYSTEM/GALAXY_ORCHESTRATOR/galaxy-master-simple.sh' param1=status terminal=true"

echo "---"
echo "🔧 System Info"
echo "---"
echo "📁 Logs Dir | bash='open' param1='/Volumes/Z7S/development/GalaxyDevelopers/DEVELOPER_SYSTEM/GALAXY_ORCHESTRATOR/logs' terminal=false"
echo "⚙️ Config Dir | bash='open' param1='/Volumes/Z7S/development/GalaxyDevelopers/DEVELOPER_SYSTEM/GALAXY_ORCHESTRATOR/config' terminal=false"

echo "---"
echo "🔄 Refresh | refresh=true"