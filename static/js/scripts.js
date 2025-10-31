const appState = {
    filterOptions: { province: [], property: [], type: [], rank_type: [] },
    selectedFilters: { province: [], property: [], type: [], rank_type: [] },
    colorMaps: { type: {}, province: {}, property: {}, rank_type: {}, affiliation: {}, ratio: {} },
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
    assignUniqueColors(typeList, provinceList, propertyList, rankTypeList, affiliationList) {
        const colorPool = utils.generateDistinctColors(
            typeList.length + provinceList.length + propertyList.length + 
            rankTypeList.length + affiliationList.length + 10
        );
        let index = 0;
        
        appState.colorMaps.type = Object.fromEntries(typeList.map((t) => [t, colorPool[index++]]));
        appState.colorMaps.province = Object.fromEntries(provinceList.map((p) => [p, colorPool[index++]]));
        appState.colorMaps.property = Object.fromEntries(propertyList.map((f) => [f, colorPool[index++]]));
        appState.colorMaps.rank_type = Object.fromEntries(rankTypeList.map((r) => [r, colorPool[index++]]));
        appState.colorMaps.affiliation = Object.fromEntries(affiliationList.map((a) => [a, colorPool[index++]]));
    }
};
const filterModule = {
    init() {
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
    },
    initSearchableSelect(selectId, inputId, dropdownId, placeholder, filterType) {
        const input = document.getElementById(inputId);
        const select = document.getElementById(selectId);
        const dropdown = document.getElementById(dropdownId);
        const renderOptions = (filterText = '') => {
            dropdown.innerHTML = '';
            // 全选选项
            const allDiv = document.createElement('div');
            allDiv.textContent = '全部';
            allDiv.onclick = () => {
                input.value = '';
                select.value = '';
                appState.selectedFilters[filterType] = [];
                dropdown.style.display = 'none';
                chartModule.fetchChartData();
                chartModule.fetchUniversityTableData();
            };
            dropdown.appendChild(allDiv);

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
                    chartModule.fetchWordcloudData();
                    chartModule.fetchMajorWordcloudData();
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
                chartModule.fetchUniversityTableData();
            }
        });
        renderOptions();
    },
    fetchFilterOptions() {
        return fetch('/get_options')
            .then(response => response.json())
            .then(data => {
                // 合并level和property选项
                const combinedProperty = [...(data.property || []), ...(data.level || [])];
                
                appState.filterOptions = {
                    province: data.province,
                    property: combinedProperty,
                    type: data.type,
                    rank_type: data.rank_type || [],
                    affiliation: data.affiliation || [],
                    year: data.year || []
                };
                colorManager.assignUniqueColors(
                    appState.filterOptions.type,
                    appState.filterOptions.province,
                    appState.filterOptions.property,
                    appState.filterOptions.rank_type,
                    appState.filterOptions.affiliation
                );
                this.init();
                return data;
            });
    }
};
const chartModule = {
    init() {
        // 初始化所有图表
        this.pieChart = echarts.init(document.getElementById('chart-pie'));
        this.mapChart = echarts.init(document.getElementById('chart-map'));
        this.levelChart = echarts.init(document.getElementById('chart-level'));
        this.rankChart = echarts.init(document.getElementById('chart-rank'));
        
        this.initChartOptions();
        this.initMapClickEvents();
        this.initPieClickEvents();
        window.addEventListener('resize', () => this.handleResize());
    },
    // 颜色线性插值辅助函数
    getGradientColor(ratio, startColor, endColor) {
        // 将十六进制颜色转换为RGB
        const hexToRgb = (hex) => {
            const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
            return result ? {
                r: parseInt(result[1], 16),
                g: parseInt(result[2], 16),
                b: parseInt(result[3], 16)
            } : null;
        };
        
        // 将RGB转换为十六进制
        const rgbToHex = (r, g, b) => {
            return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
        };
        
        const startRgb = hexToRgb(startColor);
        const endRgb = hexToRgb(endColor);
        
        if (!startRgb || !endRgb) return startColor;
        
        const r = Math.round(startRgb.r + (endRgb.r - startRgb.r) * ratio);
        const g = Math.round(startRgb.g + (endRgb.g - startRgb.g) * ratio);
        const b = Math.round(startRgb.b + (endRgb.b - startRgb.b) * ratio);
        
        return rgbToHex(r, g, b);
    },
    // 生成随机颜色函数
    generateRandomColor() {
        const colors = [
            '#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57',
            '#ff9ff3', '#54a0ff', '#5f27cd', '#00d2d3', '#ff9f43',
            '#10ac84', '#ee5a24', '#0984e3', '#6c5ce7', '#a29bfe',
            '#fd79a8', '#fdcb6e', '#e17055', '#00b894', '#e84393'
        ];
        return colors[Math.floor(Math.random() * colors.length)];
    },
    initChartOptions() {
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
        
        this.mapOption = {
            tooltip: {
                trigger: 'item',
                formatter: '{b}<br/>院校数量: {c}'
            },
            visualMap: {
                min: 0,
                max: 200,
                left: 'left',
                top: 'bottom',
                text: ['多','少'],
                inRange: {
                    color: ['#e0f7fa', '#26a69a', '#00695c']
                },
                calculable: true,
                textStyle: { color: '#fff' }
            },
            series: [{
                name: '省份院校数量分布',
                type: 'map',
                map: 'china',
                roam: false,
                zoom: 1.25,
                label: {
                    show: false,
                    color: '#fff'
                },
                emphasis: {
                    label: { show: true, color: '#fff' }
                },
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
                    show: false, // 隐藏滑条显示
                    xAxisIndex: [0],
                    start: 0,
                    end: 15, // 默认显示15个数据点
                    minSpan: 15, // 最小显示15个数据点
                    maxSpan: 15, // 最大显示15个数据点
                    height: 0, // 高度设为0隐藏
                    bottom: 0
                },
                {
                    type: 'inside',
                    xAxisIndex: [0],
                    start: 0,
                    end: 15,
                    minSpan: 15,
                    maxSpan: 15,
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
        
    },
    initMapClickEvents() {
        // 为地图添加点击事件
        this.mapChart.on('click', (params) => {
            if (params.componentType === 'series' && params.seriesType === 'map') {
                const provinceName = params.name;
                this.toggleProvinceSelection(provinceName);
            }
        });
    },
    toggleProvinceSelection(provinceName) {
        const currentSelections = appState.selectedFilters.province || [];
        
        if (currentSelections.includes(provinceName)) {
            // 如果已选中，则取消选择
            appState.selectedFilters.province = currentSelections.filter(item => item !== provinceName);
        } else {
            // 如果未选中，则添加选择
            appState.selectedFilters.province = [...currentSelections, provinceName];
        }
        
        // 更新图表数据
        this.fetchChartData();
        this.fetchUniversityTableData();
    },
    initPieClickEvents() {
        // 为饼图添加点击事件
        this.pieChart.on('click', (params) => {
            if (params.componentType === 'series' && params.seriesType === 'pie') {
                const typeName = params.name;
                this.toggleTypeSelection(typeName);
            }
        });
    },
    toggleTypeSelection(typeName) {
        const currentSelections = appState.selectedFilters.type || [];
        
        if (currentSelections.includes(typeName)) {
            // 如果已选中，则取消选择
            appState.selectedFilters.type = currentSelections.filter(item => item !== typeName);
        } else {
            // 如果未选中，则添加选择
            appState.selectedFilters.type = [...currentSelections, typeName];
        }
        
        // 更新图表数据
        this.fetchChartData();
        this.fetchUniversityTableData();
    },
    fetchChartData() {
        // 重点：如果rank_type未选或为“全部”，传空数组
        let rankTypeForFilter = appState.selectedFilters.rank_type;
        if (!rankTypeForFilter.length || rankTypeForFilter[0] === '全部') {
            rankTypeForFilter = [];
        }
        return utils.fetchData('/get_chart_data', {
            province: appState.selectedFilters.province,
            property: appState.selectedFilters.property,
            type: appState.selectedFilters.type,
            rank_type: rankTypeForFilter
        }).then(data => {
            if (data) {
                this.updatePieChart(data.chart_data);
                this.updateMapChart(data.bar_data);
                this.updateLevelBarChart(data.level_data || []);
                // 重点：updateRankChart 传递当前rank_type
                let rankType = appState.selectedFilters.rank_type[0];
                if (!rankType || rankType === '全部') {
                    rankType = '中国大学排名（主榜）';
                }
                this.updateRankChart(data.rank_data || [], rankType);
            }
        });
    },
    fetchUniversityTableData() {
        return utils.fetchData('/get_university_table_data', {
            province: appState.selectedFilters.province,
            property: appState.selectedFilters.property,
            type: appState.selectedFilters.type,
            rank_type: appState.selectedFilters.rank_type
        }).then(data => {
            if (data) {
                this.updateUniversityTable(data);
            }
        });
    },
    // 原有图表更新方法
    updatePieChart(data) {
        // 为院校类型分布创建渐变色配置
        const maxValue = Math.max(...data.map(item => item.value));
        const minValue = Math.min(...data.map(item => item.value));
        
        // 生成随机颜色（从白色渐变到随机颜色）
        const randomColor = this.generateRandomColor();
        
        // 处理饼图数据，为选中的类型添加特殊样式
        const selectedTypes = appState.selectedFilters.type || [];
        
        this.pieOption.series[0].data = data.map(item => {
            // 根据数值在最大值和最小值之间进行线性插值
            const ratio = maxValue === minValue ? 0.5 : (item.value - minValue) / (maxValue - minValue);
            // 从白色渐变到随机颜色
            const color = this.getGradientColor(ratio, '#ffffff', randomColor);
            
            const isSelected = selectedTypes.includes(item.name);
            
            return {
                ...item,
                itemStyle: { 
                    color: isSelected ? '#74b9ff' : color,
                    borderColor: isSelected ? '#fff' : 'transparent',
                    borderWidth: isSelected ? 2 : 0
                }
            };
        });
        
        this.pieChart.setOption(this.pieOption);
    },
    updateMapChart(data) {
        if (!this.mapChart) {
            console.error('地图图表未初始化');
            return;
        }
        
        // 处理地图数据，为选中的省份添加特殊样式
        const selectedProvinces = appState.selectedFilters.province || [];
        const processedData = data.map(item => {
            const isSelected = selectedProvinces.includes(item.name);
            return {
                ...item,
                itemStyle: isSelected ? {
                    areaColor: '#74b9ff',
                    borderColor: '#fff',
                    borderWidth: 2
                } : {}
            };
        });
        
        this.mapOption.series[0].data = processedData;
        const maxValue = Math.max(1, ...data.map(item => item.value));
        this.mapOption.visualMap.max = Math.ceil(maxValue / 10) * 10;
        
        // 为地图图表生成随机颜色渐变
        const randomColor = this.generateRandomColor();
        this.mapOption.visualMap.inRange.color = ['#ffffff', randomColor];
        
        this.mapChart.setOption(this.mapOption);
    },
    updateLevelBarChart(data) {
        // 为办学层次分布创建渐变色配置
        const maxValue = Math.max(...data.map(item => item.value));
        const minValue = Math.min(...data.map(item => item.value));
        
        // 生成随机颜色（从白色渐变到随机颜色）
        const randomColor = this.generateRandomColor();
        
        this.levelBarOption.series[0].data = data.map(item => {
            // 根据数值在最大值和最小值之间进行线性插值
            const ratio = maxValue === minValue ? 0.5 : (item.value - minValue) / (maxValue - minValue);
            // 从白色渐变到随机颜色
            const color = this.getGradientColor(ratio, '#ffffff', randomColor);
            
            return {
                value: item.value,
                itemStyle: { color: color }
            };
        });
        
        this.levelChart.setOption(this.levelBarOption);
    },
    updateRankChart(data, rankType) {
        if (!data || data.length === 0) {
            this.rankChart.setOption(this.rankOption);
            return;
        }
        data.sort((a, b) => b.score - a.score);
        // 图表包含所有数据，但通过dataZoom控制显示范围
        this.rankOption.xAxis.data = data.map(item => item.name);
        this.rankOption.series[0].data = data.map(item => item.score);
        const totalItems = data.length;
        
        if (totalItems <= 15) {
            // 如果数据少于等于15个，显示所有数据
            this.rankOption.dataZoom[0].start = 0;
            this.rankOption.dataZoom[0].end = 100;
            this.rankOption.dataZoom[0].minSpan = 100;
            this.rankOption.dataZoom[0].maxSpan = 100;
            this.rankOption.dataZoom[1].start = 0;
            this.rankOption.dataZoom[1].end = 100;
            this.rankOption.dataZoom[1].minSpan = 100;
            this.rankOption.dataZoom[1].maxSpan = 100;
            console.log(`数据≤15个，显示所有: ${totalItems}个`);
        } else {
            // 如果数据超过15个，显示前15个，可以左右拖动
            const spanPercent = (15 / totalItems) * 100;
            this.rankOption.dataZoom[0].start = 0;
            this.rankOption.dataZoom[0].end = spanPercent;
            this.rankOption.dataZoom[0].minSpan = spanPercent;
            this.rankOption.dataZoom[0].maxSpan = spanPercent;
            this.rankOption.dataZoom[1].start = 0;
            this.rankOption.dataZoom[1].end = spanPercent;
            this.rankOption.dataZoom[1].minSpan = spanPercent;
            this.rankOption.dataZoom[1].maxSpan = spanPercent;
            console.log(`数据>15个，显示15个, 可左右拖动查看其他数据`);
        }
        
        this.rankChart.setOption(this.rankOption);
    },
    updateUniversityTable(data) {
        const tbody = document.getElementById('university-table-body');
        
        if (!tbody) return;
        
        // 清空表格内容
        tbody.innerHTML = '';
        
        // 填充数据
        data.forEach((university, index) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${university.name}</td>
                <td>${university.province || '-'}</td>
                <td>${university.type || '-'}</td>
                <td>${university.level || '-'}</td>
            `;
            tbody.appendChild(row);
        });
    },
    
    handleResize() {
        // 所有图表响应窗口大小变化
        this.pieChart.resize();
        this.mapChart.resize();
        this.levelChart.resize();
        this.rankChart.resize();
    }
};
window.addEventListener('DOMContentLoaded', function() {
    chartModule.init();
    filterModule.fetchFilterOptions().then(() => {
        chartModule.fetchChartData();
        overviewModule.fetchOverviewData();
        chartModule.fetchUniversityTableData(); // 初始化大学表格数据
    });
});