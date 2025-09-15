const appState = {
    filterOptions: { province: [], property: [], type: [], level: [], rank_type: [] },
    selectedFilters: { province: [], property: [], type: [], level: [], rank_type: [] },
    colorMaps: { type: {}, province: {}, property: {}, level: {}, rank_type: {}, affiliation: {}, ratio: {} },
    currentSubjectType: '顶尖学科',
    currentMajorType: 'A+专业'
};
const utils = {
    generateDistinctColors(total) {
        const colors = [];
        const saturation = 70 + Math.random() * 20;
        const lightness = 50 + Math.random() * 10;
        for (let i = 0; i < total; i++) {
            const hue = Math.floor((360 / total) * i + Math.random() * 10) % 360;
            colors.push(`hsl(${hue},${saturation}%,${lightness}%)`);
        }
        for (let i = colors.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [colors[i], colors[j]] = [colors[j], colors[i]];
        }
        return colors;
    },
    fetchData(url, data = {}) {
        return fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        }).then(response => response.json())
            .catch(error => {
                console.error(`请求${url}失败:`, error);
                return;
            });
    }
};
const colorManager = {
    assignUniqueColors(typeList, provinceList, propertyList, levelList, rankTypeList, affiliationList) {
        const colorPool = utils.generateDistinctColors(
            typeList.length + provinceList.length + propertyList.length + 
            levelList.length + rankTypeList.length + affiliationList.length + 10
        );
        let index = 0;
        
        appState.colorMaps.type = Object.fromEntries(typeList.map((t) => [t, colorPool[index++]]));
        appState.colorMaps.province = Object.fromEntries(provinceList.map((p) => [p, colorPool[index++]]));
        appState.colorMaps.property = Object.fromEntries(propertyList.map((f) => [f, colorPool[index++]]));
        appState.colorMaps.level = Object.fromEntries(levelList.map((l) => [l, colorPool[index++]]));
        appState.colorMaps.rank_type = Object.fromEntries(rankTypeList.map((r) => [r, colorPool[index++]]));
        appState.colorMaps.affiliation = Object.fromEntries(affiliationList.map((a) => [a, colorPool[index++]]));
    }
};
const filterModule = {
    init() {
        this.initSearchableSelect(
            'search-province', 
            'search-province-input', 
            'search-province-dropdown', 
            '搜索省份...', 
            'province'
        );
        this.initSearchableSelect(
            'search-type', 
            'search-type-input', 
            'search-type-dropdown', 
            '搜索院校类型...', 
            'type'
        );
        this.initSearchableSelect(
            'search-level', 
            'search-level-input', 
            'search-level-dropdown', 
            '搜索办学层次...', 
            'level'
        );
        this.initSearchableSelect(
            'search-property', 
            'search-property-input', 
            'search-property-dropdown', 
            '搜索院校特性...', 
            'property'
        );
        this.initSearchableSelect(
            'search-rank-type', 
            'search-rank-type-input', 
            'search-rank-type-dropdown', 
            '搜索排名类型...', 
            'rank_type'
        );
        
        // 初始化学科类型选择器
        this.initSubjectTypeSelector();
        
        // 初始化专业类型选择器
        this.initMajorTypeSelector();
    },
    initSubjectTypeSelector() {
        const buttons = document.querySelectorAll('#chart-wordcloud .subject-type-btn');
        buttons.forEach(btn => {
            btn.addEventListener('click', () => {
                // 移除所有按钮的active类
                buttons.forEach(b => b.classList.remove('active'));
                // 给当前点击的按钮添加active类
                btn.classList.add('active');
                // 更新当前选择的学科类型
                appState.currentSubjectType = btn.dataset.type;
                // 更新显示的标签
                document.getElementById('subject-type-label').textContent = appState.currentSubjectType;
                // 获取词云数据
                chartModule.fetchWordcloudData();
            });
        });
    },
    initMajorTypeSelector() {
        const buttons = document.querySelectorAll('#chart-major-wordcloud .subject-type-btn');
        buttons.forEach(btn => {
            btn.addEventListener('click', () => {
                // 移除所有按钮的active类
                buttons.forEach(b => b.classList.remove('active'));
                // 给当前点击的按钮添加active类
                btn.classList.add('active');
                // 更新当前选择的专业类型
                appState.currentMajorType = btn.dataset.type;
                // 更新显示的标签
                document.getElementById('major-type-label').textContent = appState.currentMajorType;
                // 获取专业词云数据
                chartModule.fetchMajorWordcloudData();
            });
        });
    },
    initSearchableSelect(selectId, inputId, dropdownId, placeholder, filterType) {
        const input = document.getElementById(inputId);
        const select = document.getElementById(selectId);
        const dropdown = document.getElementById(dropdownId);
        const renderOptions = (filterText = '') => {
            dropdown.innerHTML = '';
            const options = appState.filterOptions[filterType] || [];
            const filteredOptions = options.filter(option => 
                option.toLowerCase().includes(filterText.toLowerCase())
            );
            if (filteredOptions.length === 0) {
                const noResult = document.createElement('div');
                noResult.textContent = '无匹配结果';
                dropdown.appendChild(noResult);
                return;
            }
            filteredOptions.forEach(option => {
                const div = document.createElement('div');
                div.textContent = option;
                div.onclick = () => {
                    input.value = option;
                    select.value = option;
                    dropdown.style.display = 'none';
                    appState.selectedFilters[filterType] = [option];
                    chartModule.fetchChartData();
                    overviewModule.fetchOverviewData();
                    chartModule.fetchWordcloudData();
                    chartModule.fetchMajorWordcloudData(); // 添加专业词云数据更新
                };
                dropdown.appendChild(div);
            });
        };
        input.addEventListener('focus', () => {
            if (dropdown.children.length === 0) {
                renderOptions();
            }
            dropdown.style.display = 'block';
        });
        input.addEventListener('input', (e) => renderOptions(e.target.value));
        input.addEventListener('blur', () => {
            setTimeout(() => dropdown.style.display = 'none', 200);
        });
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                input.value = '';
                select.value = '';
                appState.selectedFilters[filterType] = [];
                dropdown.style.display = 'none';
                chartModule.fetchChartData();
                overviewModule.fetchOverviewData();
                chartModule.fetchWordcloudData();
                chartModule.fetchMajorWordcloudData(); // 添加专业词云数据更新
            }
        });
        renderOptions();
    },
    fetchFilterOptions() {
        return fetch('/get_options')
            .then(response => response.json())
            .then(data => {
                appState.filterOptions = {
                    province: data.province,
                    property: data.property,
                    type: data.type,
                    level: data.level,
                    rank_type: data.rank_type || [],
                    affiliation: data.affiliation || [],
                    year: data.year || []
                };
                colorManager.assignUniqueColors(
                    appState.filterOptions.type,
                    appState.filterOptions.province,
                    appState.filterOptions.property,
                    appState.filterOptions.level,
                    appState.filterOptions.rank_type,
                    appState.filterOptions.affiliation
                );
                this.init();
                return data;
            });
    }
};
const overviewModule = {
    fetchOverviewData() {
        return utils.fetchData('/get_overview', {
            province: appState.selectedFilters.province,
            property: appState.selectedFilters.property,
            type: appState.selectedFilters.type,
            level: appState.selectedFilters.level,
            rank_type: appState.selectedFilters.rank_type
        }).then(data => {
            if (data) {
                document.getElementById('overview-total').textContent = data.total;
                document.getElementById('overview-benke').textContent = data.benke;
                document.getElementById('overview-985').textContent = data['985'];
                document.getElementById('overview-211').textContent = data['211'];
                document.getElementById('overview-doubletop').textContent = data.doubletop;
            }
        });
    }
};
const chartModule = {
    init() {
        // 初始化所有图表
        this.pieChart = echarts.init(document.getElementById('chart-pie'));
        this.treemapChart = echarts.init(document.getElementById('chart-treemap'));
        this.levelChart = echarts.init(document.getElementById('chart-level'));
        this.rankChart = echarts.init(document.getElementById('chart-rank'));
        this.wordcloudChart = echarts.init(document.getElementById('wordcloud-chart'));
        this.majorWordcloudChart = echarts.init(document.getElementById('major-wordcloud-chart'));
        
        this.initChartOptions();
        window.addEventListener('resize', () => this.handleResize());
    },
    initChartOptions() {
        // 原有图表配置保持不变...
        this.pieOption = {
            tooltip: { trigger: 'item', formatter: '{b}: {c}所 ({d}%)' },
            series: [{
                name: '院校类型分布',
                type: 'pie',
                radius: ['20%', '80%'],
                roseType: 'area',
                avoidLabelOverlap: false,
                itemStyle: { borderRadius: 10, borderColor: '#0c2461', borderWidth: 2 },
                label: { show: true, formatter: '{b}: {c}所', color: '#fff' },
                emphasis: {
                    label: { show: true, fontSize: '16', fontWeight: 'bold' },
                    itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.5)' }
                },
                labelLine: { show: true },
                data: []
            }],
            backgroundColor: 'transparent'
        };
        
        this.treemapOption = {
            tooltip: { formatter: '{b}: {c}所' },
            series: [{
                type: 'treemap',
                roam: false,
                nodeClick: false,
                label: {
                    show: true,
                    formatter: '{b}\n{c}所',
                    color: '#fff',
                    fontSize: 16,
                    fontWeight: 'bold'
                },
                itemStyle: { gapWidth: 1 },
                upperLabel: { show: false },
                breadcrumb: { show: false },
                data: []
            }],
            backgroundColor: 'transparent'
        };
        
        this.levelBarOption = {
            tooltip: { 
                trigger: 'axis', 
                axisPointer: { type: 'shadow' },
                formatter: '{b}: {c}所'
            },
            xAxis: {
                type: 'category',
                data: ["普通本科", "职业本科", "高职（专科）"],
                axisLabel: { color: '#fff', fontWeight: 'bold' }
            },
            yAxis: { type: 'value', axisLabel: { color: '#fff' } },
            series: [{
                name: '办学层次分布',
                type: 'bar',
                barWidth: 50,
                itemStyle: { borderRadius: [8, 8, 0, 0] },
                label: {
                    show: true,
                    position: 'top',
                    color: '#fff',
                    fontWeight: 'bold',
                    formatter: '{c}'
                },
                data: []
            }],
            backgroundColor: 'transparent'
        };
        
        this.rankOption = {
            tooltip: {
                trigger: 'axis',
                formatter: function(params) {
                    const data = params[0];
                    return `${data.name}<br/>排名: ${data.dataIndex + 1}<br/>得分: ${data.value}`;
                }
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '3%',
                top: '15%',
                containLabel: true
            },
            dataZoom: [
                {
                    type: 'slider',
                    show: true,
                    xAxisIndex: [0],
                    start: 0,
                    end: 50, // 默认显示50个
                    height: 20,
                    bottom: 10,
                    handleIcon: 'M10.7,11.9v-1.3H9.3v1.3c-4.9,0.3-8.8,4.4-8.8,9.4c0,5,3.9,9.1,8.8,9.4v1.3h1.3v-1.3c4.9-0.3,8.8-4.4,8.8-9.4C19.5,16.3,15.6,12.2,10.7,11.9z M13.3,24.4H6.7V23h6.6V24.4z M13.3,19.6H6.7v-1.4h6.6V19.6z',
                    handleSize: '80%',
                    handleStyle: {
                        color: '#fff',
                        shadowBlur: 3,
                        shadowColor: 'rgba(0, 0, 0, 0.6)',
                        shadowOffsetX: 2,
                        shadowOffsetY: 2
                    }
                },
                {
                    type: 'inside',
                    xAxisIndex: [0],
                    start: 0,
                    end: 50,
                    zoomOnMouseWheel: false,
                    moveOnMouseMove: true,
                    moveOnMouseWheel: true
                }
            ],
            xAxis: {
                type: 'category',
                data: [],
                axisLabel: {
                    color: '#fff',
                    interval: 0,
                    rotate: 45,
                    formatter: function(value) {
                        // 如果标签太长，截断显示
                        return value.length > 8 ? value.substring(0, 8) + '...' : value;
                    }
                },
                axisLine: { lineStyle: { color: '#fff' } }
            },
            yAxis: {
                type: 'value',
                name: '得分',
                nameTextStyle: { color: '#fff' },
                axisLabel: { color: '#fff' },
                axisLine: { lineStyle: { color: '#fff' } },
                splitLine: { lineStyle: { color: 'rgba(255,255,255,0.2)' } }
            },
            series: [{
                name: '得分',
                type: 'line',
                data: [],
                symbol: 'circle',
                symbolSize: 8,
                itemStyle: {
                    color: '#ffcc00',
                    borderColor: '#fff',
                    borderWidth: 2
                },
                lineStyle: {
                    width: 3,
                    color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                        { offset: 0, color: '#ffcc00' },
                        { offset: 1, color: '#ff9900' }
                    ])
                },
                emphasis: {
                    itemStyle: {
                        color: '#ff6600',
                        borderColor: '#fff',
                        borderWidth: 3
                    }
                },
                markPoint: {
                    data: [
                        { type: 'max', name: '最高分' },
                        { type: 'min', name: '最低分' }
                    ],
                    label: { color: '#fff' },
                    itemStyle: { color: '#ff4d4f' }
                },
                markLine: {
                    data: [{ type: 'average', name: '平均分' }],
                    label: { color: '#fff' },
                    lineStyle: { color: '#1890ff' }
                }
            }],
            backgroundColor: 'transparent'
        };
        
        // 学科词云图配置
        this.wordcloudOption = {
            tooltip: {
                show: true,
                formatter: function (params) {
                    return `${params.name}: ${params.value}个${appState.currentSubjectType}`;
                }
            },
            series: [{
                type: 'wordCloud',
                shape: 'circle',
                left: 'center',
                top: 'center',
                width: '90%',
                height: '90%',
                sizeRange: [12, 60],
                rotationRange: [-45, 45],
                rotationStep: 45,
                gridSize: 8,
                drawOutOfBound: false,
                textStyle: {
                    color: function () {
                        return 'rgb(' + [
                            Math.round(Math.random() * 160),
                            Math.round(Math.random() * 160),
                            Math.round(Math.random() * 160)
                        ].join(',') + ')';
                    }
                },
                emphasis: {
                    focus: 'self',
                    textStyle: {
                        shadowBlur: 10,
                        shadowColor: '#333'
                    }
                },
                data: []
            }],
            backgroundColor: 'transparent'
        };
        
        // 专业词云图配置
        this.majorWordcloudOption = {
            tooltip: {
                show: true,
                formatter: function (params) {
                    return `${params.name}: ${params.value}个${appState.currentMajorType}`;
                }
            },
            series: [{
                type: 'wordCloud',
                shape: 'circle',
                left: 'center',
                top: 'center',
                width: '90%',
                height: '90%',
                sizeRange: [12, 60],
                rotationRange: [-45, 45],
                rotationStep: 45,
                gridSize: 8,
                drawOutOfBound: false,
                textStyle: {
                    color: function () {
                        return 'rgb(' + [
                            Math.round(Math.random() * 160),
                            Math.round(Math.random() * 160),
                            Math.round(Math.random() * 160)
                        ].join(',') + ')';
                    }
                },
                emphasis: {
                    focus: 'self',
                    textStyle: {
                        shadowBlur: 10,
                        shadowColor: '#333'
                    }
                },
                data: []
            }],
            backgroundColor: 'transparent'
        };
    },
    fetchChartData() {
        return utils.fetchData('/get_chart_data', {
            province: appState.selectedFilters.province,
            property: appState.selectedFilters.property,
            type: appState.selectedFilters.type,
            level: appState.selectedFilters.level,
            rank_type: appState.selectedFilters.rank_type
        }).then(data => {
            if (data) {
                // 更新原有图表
                this.updatePieChart(data.chart_data);
                this.updateTreemapChart(data.bar_data);
                this.updateLevelBarChart(data.level_data || []);
                this.updateRankChart(data.rank_data || []);
                
                // 更新统计数字
                document.getElementById('type-count').textContent = data.chart_data.length;
                document.getElementById('province-count').textContent = data.bar_data.length;
                document.getElementById('rank-count').textContent = Math.min(50, data.rank_data ? data.rank_data.length : 0);
            }
        });
    },
    fetchWordcloudData() {
        return utils.fetchData('/get_wordcloud_data', {
            province: appState.selectedFilters.province,
            property: appState.selectedFilters.property,
            type: appState.selectedFilters.type,
            level: appState.selectedFilters.level,
            rank_type: appState.selectedFilters.rank_type,
            subject_type: appState.currentSubjectType
        }).then(data => {
            if (data) {
                this.updateWordcloudChart(data);
            }
        });
    },
    fetchMajorWordcloudData() {
        return utils.fetchData('/get_major_wordcloud_data', {
            province: appState.selectedFilters.province,
            property: appState.selectedFilters.property,
            type: appState.selectedFilters.type,
            level: appState.selectedFilters.level,
            rank_type: appState.selectedFilters.rank_type,
            major_type: appState.currentMajorType
        }).then(data => {
            if (data) {
                this.updateMajorWordcloudChart(data);
            }
        });
    },
    // 原有图表更新方法
    updatePieChart(data) {
        this.pieOption.series[0].data = data.map(item => ({
            ...item,
            itemStyle: { color: appState.colorMaps.type[item.name] }
        }));
        this.pieOption.color = appState.filterOptions.type.map(t => appState.colorMaps.type[t]);
        this.pieChart.setOption(this.pieOption);
    },
    updateTreemapChart(data) {
        this.treemapOption.series[0].data = data.map(item => ({
            name: item.name,
            value: item.value,
            itemStyle: { color: appState.colorMaps.province[item.name] }
        }));
        this.treemapChart.setOption(this.treemapOption);
    },
    updateLevelBarChart(data) {
        this.levelBarOption.series[0].data = data.map(item => ({
            value: item.value,
            itemStyle: { color: appState.colorMaps.level[item.name] }
        }));
        this.levelChart.setOption(this.levelBarOption);
    },
    updateRankChart(data) {
        if (!data || data.length === 0) {
            this.rankChart.setOption(this.rankOption);
            return;
        }
        
        // 根据筛选的排名类型设置标题
        const rankType = appState.selectedFilters.rank_type[0] || '中国大学排名（主榜）';
        document.getElementById('rank-chart-title').textContent = `${rankType}`;
        
        // 按得分降序排序
        data.sort((a, b) => b.score - a.score);
        
        // 只取前50名
        const displayData = data.slice(0, 50);
        
        this.rankOption.xAxis.data = displayData.map(item => item.name);
        this.rankOption.series[0].data = displayData.map(item => item.score);
        
        // 更新dataZoom范围
        const totalItems = data.length;
        const visibleItems = Math.min(50, totalItems);
        this.rankOption.dataZoom[0].end = (visibleItems / totalItems) * 100;
        this.rankOption.dataZoom[1].end = (visibleItems / totalItems) * 100;
        
        this.rankChart.setOption(this.rankOption);
    },
    updateWordcloudChart(data) {
        this.wordcloudOption.series[0].data = data;
        this.wordcloudChart.setOption(this.wordcloudOption);
    },
    updateMajorWordcloudChart(data) {
        this.majorWordcloudOption.series[0].data = data;
        this.majorWordcloudChart.setOption(this.majorWordcloudOption);
    },
    
    handleResize() {
        // 所有图表响应窗口大小变化
        this.pieChart.resize();
        this.treemapChart.resize();
        this.levelChart.resize();
        this.rankChart.resize();
        this.wordcloudChart.resize();
        this.majorWordcloudChart.resize();
    }
};
window.addEventListener('DOMContentLoaded', function() {
    chartModule.init();
    filterModule.fetchFilterOptions().then(() => {
        chartModule.fetchChartData();
        overviewModule.fetchOverviewData();
        chartModule.fetchWordcloudData();
        chartModule.fetchMajorWordcloudData(); // 初始化专业词云数据
    });
});