const chartModule = {
    init() {
        this.mapChart = echarts.init(document.getElementById('chart-map'));
        this.loadGeoJson();
        window.addEventListener('resize', () => this.mapChart.resize());
    },
    loadGeoJson() {
        // 加载中国地图的 GeoJSON 数据
        fetch('../static/json/geojson.json')
            .then(response => response.json())
            .then(geoJson => {
                echarts.registerMap('china', geoJson); // 注册地图
                this.fetchProvinceData(); // 加载省份数据
            })
            .catch(error => console.error('加载地图数据失败:', error));
    },
    fetchProvinceData() {
        // 获取省份数据
        fetch('/get_province_data')
            .then(response => response.json())
            .then(data => this.updateMapChart(data))
            .catch(error => console.error('加载省份数据失败:', error));
    },
    updateMapChart(data) {
        // 更新地图数据
        const option = {
            tooltip: { trigger: 'item' },
            visualMap: {
                min: 0,
                max: Math.max(...data.map(item => item.value)),
                left: 'left',
                top: 'bottom',
                text: ['高', '低'],
                calculable: true,
                inRange: { color: ['#e0ffff', '#006edd'] }
            },
            series: [{
                name: '大学数量',
                type: 'map',
                map: 'china',
                roam: false,
                data
            }]
        };
        this.mapChart.setOption(option);
    }
};
window.addEventListener('DOMContentLoaded', () => chartModule.init());