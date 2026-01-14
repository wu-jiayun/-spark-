# -*- coding: utf-8 -*-
"""
沃土规划师 - 基于Spark的农业种植适宜性区划与优化系统
集成MySQL数据源和ECharts可视化
"""

from flask import Flask, render_template, request, jsonify
import pandas as pd
import json
import os
import numpy as np
from datetime import datetime
import logging
from real_data_connector import RealDataConnector
import threading
import time

# 所有的echarts图

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'spark_agricultural_system_2024'

# 全局变量
spark_connector = None
analysis_results = None
system_status = "未初始化"

# 性能优化缓存
data_cache = {}
cache_lock = threading.Lock()
CACHE_TIMEOUT = 600  # 10分钟缓存

def get_cache_key(endpoint, params=None):
    """生成缓存键"""
    if params:
        param_str = json.dumps(params, sort_keys=True)
        return f"{endpoint}_{hash(param_str)}"
    return endpoint

def set_cache(key, data, timeout=CACHE_TIMEOUT):
    """设置缓存"""
    with cache_lock:
        data_cache[key] = {
            'data': data,
            'timestamp': time.time(),
            'timeout': timeout
        }

def get_cache(key):
    """获取缓存"""
    with cache_lock:
        if key in data_cache:
            cache_item = data_cache[key]
            if time.time() - cache_item['timestamp'] < cache_item['timeout']:
                return cache_item['data']
            else:
                del data_cache[key]
    return None

def compress_data(data):
    """压缩数据精度"""
    def round_numbers(obj):
        if isinstance(obj, dict):
            return {k: round_numbers(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [round_numbers(item) for item in obj]
        elif isinstance(obj, float):
            return round(obj, 3)
        return obj
    return round_numbers(data)

@app.route('/')
def index():
    """主页"""
    return render_template('spark_agricultural_index.html')

@app.route('/api/system/initialize', methods=['POST'])
def initialize_system():
    """初始化Spark系统"""
    global spark_connector, system_status
    
    try:
        logger.info("🚀 开始初始化Spark农业分析系统...")
        system_status = "初始化中"
        
        # 创建Spark连接器
        spark_connector = RealDataConnector()
        
        # 读取数据
        data = spark_connector.read_all_agricultural_data()
        if not data:
            system_status = "数据读取失败"
            return jsonify({
                'status': 'error',
                'message': '无法读取MySQL数据，请检查数据库连接'
            })
        
        system_status = "就绪"
        logger.info("✅ Spark系统初始化完成")
        
        return jsonify({
            'status': 'success',
            'message': 'Spark系统初始化成功',
            'data_summary': {
                'temperature_records': len(data['temperature']) if data['temperature'] is not None else 0,
                'precipitation_records': len(data['precipitation']) if data['precipitation'] is not None else 0,
                'soil_records': len(data['soil']) if data['soil'] is not None else 0,
                'crop_types': len(data['crop']) if data['crop'] is not None else 0
            }
        })
        
    except Exception as e:
        system_status = "初始化失败"
        logger.error(f"❌ 系统初始化失败: {e}")
        return jsonify({
            'status': 'error',
            'message': f'系统初始化失败: {str(e)}'
        })

@app.route('/api/system/status')
def get_system_status():
    """获取系统状态"""
    cache_key = get_cache_key('system_status')
    cached_result = get_cache(cache_key)
    if cached_result:
        return jsonify(cached_result)
    
    global system_status, spark_connector
    
    result = {
        'status': system_status,
        'spark_initialized': spark_connector is not None,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    set_cache(cache_key, result, 60)  # 缓存1分钟
    return jsonify(result)

@app.route('/api/analysis/run', methods=['POST'])
def run_comprehensive_analysis():
    """运行综合分析"""
    global spark_connector, analysis_results
    
    if not spark_connector:
        return jsonify({
            'status': 'error',
            'message': '请先初始化Spark系统'
        })
    
    try:
        start_time = time.time()
        
        # 清除缓存
        with cache_lock:
            data_cache.clear()
        
        logger.info("🔬 开始运行综合分析...")
        
        # 生成综合分析报告
        analysis_results = spark_connector.generate_comprehensive_report()
        
        if not analysis_results:
            return jsonify({
                'status': 'error',
                'message': '分析失败，请检查数据完整性'
            })
        
        execution_time = time.time() - start_time
        
        # 统计分析结果
        stats = {
            'temperature_analysis': len(analysis_results.get('temperature', {})),
            'soil_analysis': len(analysis_results.get('soil', {})),
            'crop_analysis': len(analysis_results.get('crop', {})),
            'execution_time': round(execution_time, 2)
        }
        
        logger.info("✅ 综合分析完成")
        
        return jsonify({
            'status': 'success',
            'message': '综合分析完成',
            'statistics': stats
        })
        
    except Exception as e:
        logger.error(f"❌ 分析失败: {e}")
        return jsonify({
            'status': 'error',
            'message': f'分析失败: {str(e)}'
        })

@app.route('/api/echarts/climate_trends')
def get_climate_trends():
    """获取气候趋势ECharts数据"""
    cache_key = get_cache_key('climate_trends')
    cached_result = get_cache(cache_key)
    if cached_result:
        return jsonify(cached_result)
    
    global analysis_results
    
    if not analysis_results or 'temperature' not in analysis_results:
        return jsonify({
            'status': 'error',
            'message': '请先运行综合分析'
        })
    
    try:
        start_time = time.time()
        temp_data = analysis_results['temperature']
        
        # 月度温度趋势图
        monthly_pattern = temp_data['monthly_pattern']
        temp_chart = {
            'title': '月度温度变化趋势',
            'xAxis': monthly_pattern['month_name'].tolist(),
            'series': [
                {
                    'name': '平均温度',
                    'type': 'line',
                    'data': monthly_pattern['avg_temp'].tolist(),
                    'smooth': True
                }
            ]
        }
        
        # 年度温度趋势（如果有数据）
        annual_trend = temp_data.get('annual_trend')
        annual_chart = {
            'title': '年度温度趋势',
            'xAxis': [],
            'series': []
        }
        
        if annual_trend is not None and not annual_trend.empty:
            annual_chart['xAxis'] = annual_trend['year_val'].tolist()
            annual_chart['series'] = [
                {
                    'name': '年平均温度',
                    'type': 'line',
                    'data': annual_trend['annual'].dropna().tolist(),
                    'smooth': True
                }
            ]
        
        # 季节温度对比
        seasonal_chart = {
            'title': '季节温度对比',
            'data': []
        }
        
        if annual_trend is not None and not annual_trend.empty:
            seasons = ['winter', 'spring', 'summer', 'autumn']
            season_names = ['冬季', '春季', '夏季', '秋季']
            
            for i, season in enumerate(seasons):
                if season in annual_trend.columns:
                    avg_temp = annual_trend[season].mean()
                    if not pd.isna(avg_temp):
                        seasonal_chart['data'].append({
                            'name': season_names[i],
                            'value': round(avg_temp, 2)
                        })
        
        processing_time = time.time() - start_time
        
        result = {
            'status': 'success',
            'charts': {
                'temperature_trend': temp_chart,
                'annual_trend': annual_chart,
                'seasonal_comparison': seasonal_chart
            },
            'processing_time': round(processing_time, 3)
        }
        
        # 压缩数据
        result = compress_data(result)
        
        # 缓存结果
        set_cache(cache_key, result)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ 气候趋势数据生成失败: {e}")
        return jsonify({
            'status': 'error',
            'message': f'气候趋势数据生成失败: {str(e)}'
        })

@app.route('/api/echarts/soil_analysis')
def get_soil_analysis():
    """获取土壤分析ECharts数据"""
    cache_key = get_cache_key('soil_analysis')
    cached_result = get_cache(cache_key)
    if cached_result:
        return jsonify(cached_result)
    
    global analysis_results
    
    if not analysis_results or 'soil' not in analysis_results:
        return jsonify({
            'status': 'error',
            'message': '请先运行综合分析'
        })
    
    try:
        start_time = time.time()
        soil_data = analysis_results['soil']
        
        # 土壤类型分布饼图
        soil_type_dist = soil_data['soil_type_distribution']
        soil_type_summary = soil_type_dist.groupby('soil_type')['count'].sum().reset_index()
        
        soil_pie_data = []
        for _, row in soil_type_summary.iterrows():
            soil_pie_data.append({
                'name': row['soil_type'],
                'value': int(row['count'])
            })
        
        soil_pie_chart = {
            'title': '土壤类型分布',
            'data': soil_pie_data
        }
        
        # pH值分布柱状图
        ph_dist = soil_data['ph_distribution']
        ph_chart = {
            'title': 'pH值分布统计',
            'xAxis': ph_dist['ph_category'].tolist(),
            'series': [
                {
                    'name': '样本数量',
                    'type': 'bar',
                    'data': ph_dist['count'].tolist()
                }
            ]
        }
        
        # 县市土壤质量排名
        county_quality = soil_data['county_soil_quality'].head(15)  # 取前15名
        quality_chart = {
            'title': '县市土壤质量排名（前15名）',
            'xAxis': county_quality['county'].tolist(),
            'series': [
                {
                    'name': '土壤质量评分',
                    'type': 'bar',
                    'data': county_quality['soil_quality_score'].tolist()
                }
            ]
        }
        
        processing_time = time.time() - start_time
        
        result = {
            'status': 'success',
            'charts': {
                'soil_type_pie': soil_pie_chart,
                'ph_distribution': ph_chart,
                'county_quality_ranking': quality_chart
            },
            'processing_time': round(processing_time, 3)
        }
        
        # 压缩数据
        result = compress_data(result)
        
        # 缓存结果
        set_cache(cache_key, result)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ 土壤分析数据生成失败: {e}")
        return jsonify({
            'status': 'error',
            'message': f'土壤分析数据生成失败: {str(e)}'
        })

@app.route('/api/echarts/crop_suitability')
def get_crop_suitability():
    """获取作物适宜性ECharts数据"""
    cache_key = get_cache_key('crop_suitability')
    cached_result = get_cache(cache_key)
    if cached_result:
        return jsonify(cached_result)
    
    global analysis_results
    
    if not analysis_results or 'crop' not in analysis_results:
        return jsonify({
            'status': 'error',
            'message': '请先运行综合分析'
        })
    
    try:
        start_time = time.time()
        crop_data = analysis_results['crop']
        
        # 作物分类饼图
        crop_categories = crop_data['crop_categories']
        category_pie_data = []
        for _, row in crop_categories.iterrows():
            category_pie_data.append({
                'name': row['category'],
                'value': int(row['total_varieties'])
            })
        
        category_pie_chart = {
            'title': '作物分类分布',
            'data': category_pie_data
        }
        
        # 温度需求柱状图
        temp_requirements = crop_data['temperature_requirements']
        if not temp_requirements.empty:
            temp_chart = {
                'title': '作物温度需求范围',
                'xAxis': temp_requirements['crop_type'].head(10).tolist(),
                'series': [
                    {
                        'name': '最低温度',
                        'type': 'bar',
                        'data': temp_requirements['min_temperature_min'].head(10).fillna(0).tolist()
                    },
                    {
                        'name': '最高温度',
                        'type': 'bar',
                        'data': temp_requirements['max_temperature_max'].head(10).fillna(30).tolist()
                    }
                ]
            }
        else:
            temp_chart = {
                'title': '作物温度需求范围',
                'xAxis': [],
                'series': []
            }
        
        # pH需求散点图
        ph_requirements = crop_data['ph_requirements']
        if not ph_requirements.empty:
            ph_scatter_data = []
            for _, row in ph_requirements.head(20).iterrows():
                if pd.notna(row['ph_min']) and pd.notna(row['ph_max']):
                    ph_scatter_data.append([
                        float(row['ph_min']),
                        float(row['ph_max']),
                        row['crop_type']
                    ])
            
            ph_scatter_chart = {
                'title': '作物pH需求分布',
                'data': ph_scatter_data
            }
        else:
            ph_scatter_chart = {
                'title': '作物pH需求分布',
                'data': []
            }
        
        processing_time = time.time() - start_time
        
        result = {
            'status': 'success',
            'charts': {
                'suitability_distribution': category_pie_chart,
                'crop_advantages_radar': temp_chart,
                'limiting_factors_pie': ph_scatter_chart
            },
            'processing_time': round(processing_time, 3)
        }
        
        # 压缩数据
        result = compress_data(result)
        
        # 缓存结果
        set_cache(cache_key, result)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ 作物适宜性数据生成失败: {e}")
        return jsonify({
            'status': 'error',
            'message': f'作物适宜性数据生成失败: {str(e)}'
        })
        }
        
        # 最佳种植区域推荐
        best_areas = crop_data['best_planting_areas']
        
        # 按作物分组制作雷达图
        radar_data = {}
        radar_indicator = [
            {'name': '适宜面积', 'max': best_areas['suitable_points'].max()},
            {'name': '平均适宜性', 'max': 1},
            {'name': '区域集中度', 'max': 1}
        ]
        
        for crop in crops:
            crop_areas = best_areas[best_areas['crop_name'] == crop].head(5)
            if not crop_areas.empty:
                radar_data[crop] = [
                    float(crop_areas['suitable_points'].mean()),
                    float(crop_areas['avg_suitability'].mean()),
                    float(len(crop_areas) / 10)  # 标准化区域集中度
                ]
        
        radar_chart = {
            'title': '作物种植优势雷达图',
            'indicator': radar_indicator,
            'data': radar_data
        }
        
        # 限制因子分析饼图
        limiting_factors = crop_data['limiting_factors']
        factor_summary = limiting_factors.groupby('limiting_factor')['affected_areas'].sum().reset_index()
        
        factor_pie_data = []
        for _, row in factor_summary.iterrows():
            factor_pie_data.append({
                'name': row['limiting_factor'],
                'value': int(row['affected_areas'])
            })
        
        limiting_factors_chart = {
            'title': '种植限制因子分析',
            'data': factor_pie_data
        }
        
        processing_time = time.time() - start_time
        
        result = {
            'status': 'success',
            'charts': {
                'suitability_distribution': suitability_chart,
                'crop_advantages_radar': radar_chart,
                'limiting_factors_pie': limiting_factors_chart
            },
            'processing_time': round(processing_time, 3)
        }
        
        # 压缩数据
        result = compress_data(result)
        
        # 缓存结果
        set_cache(cache_key, result)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ 作物适宜性数据生成失败: {e}")
        return jsonify({
            'status': 'error',
            'message': f'作物适宜性数据生成失败: {str(e)}'
        })

@app.route('/api/echarts/zoning_optimization')
def get_zoning_optimization():
    """获取区划优化ECharts数据"""
    cache_key = get_cache_key('zoning_optimization')
    cached_result = get_cache(cache_key)
    if cached_result:
        return jsonify(cached_result)
    
    global analysis_results
    
    if not analysis_results or 'crop' not in analysis_results:
        return jsonify({
            'status': 'error',
            'message': '请先运行综合分析'
        })
    
    try:
        start_time = time.time()
        crop_data = analysis_results['crop']
        
        # 区划优化散点图
        zoning_data = crop_data['zoning_optimization']
        
        scatter_series = []
        crops = zoning_data['crop_name'].unique()
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
        
        for i, crop in enumerate(crops):
            crop_zones = zoning_data[zoning_data['crop_name'] == crop]
            scatter_data = []
            
            for _, row in crop_zones.iterrows():
                scatter_data.append([
                    float(row['zone_center_lon']),
                    float(row['zone_center_lat']),
                    float(row['avg_suitability']),
                    int(row['grid_count']),
                    str(row['zone_id'])
                ])
            
            scatter_series.append({
                'name': crop,
                'type': 'scatter',
                'data': scatter_data,
                'symbolSize': lambda params: max(5, min(30, params[3] / 10)),
                'itemStyle': {
                    'color': colors[i % len(colors)]
                }
            })
        
        zoning_scatter = {
            'title': '区划优化分布图',
            'series': scatter_series
        }
        
        # 最佳种植区域地图数据
        best_areas = crop_data['best_planting_areas']
        
        map_series = []
        for crop in crops:
            crop_areas = best_areas[best_areas['crop_name'] == crop].head(10)
            map_data = []
            
            for _, row in crop_areas.iterrows():
                map_data.append([
                    float(row['center_lon']),
                    float(row['center_lat']),
                    float(row['avg_suitability']),
                    row['county']
                ])
            
            map_series.append({
                'name': crop,
                'type': 'scatter',
                'coordinateSystem': 'geo',
                'data': map_data,
                'symbolSize': 8,
                'itemStyle': {
                    'color': colors[crops.tolist().index(crop) % len(colors)]
                }
            })
        
        optimization_map = {
            'title': '最佳种植区域分布',
            'series': map_series,
            'geo': {
                'map': 'china',
                'roam': True,
                'zoom': 1.2,
                'center': [112, 27.5],
                'itemStyle': {
                    'areaColor': '#f0f0f0',
                    'borderColor': '#999'
                }
            }
        }
        
        processing_time = time.time() - start_time
        
        result = {
            'status': 'success',
            'charts': {
                'zoning_scatter': zoning_scatter,
                'optimization_map': optimization_map
            },
            'processing_time': round(processing_time, 3)
        }
        
        # 压缩数据
        result = compress_data(result)
        
        # 缓存结果
        set_cache(cache_key, result)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ 区划优化数据生成失败: {e}")
        return jsonify({
            'status': 'error',
            'message': f'区划优化数据生成失败: {str(e)}'
        })

@app.route('/api/report/export')
def export_analysis_report():
    """导出分析报告"""
    global analysis_results
    
    if not analysis_results:
        return jsonify({
            'status': 'error',
            'message': '请先运行综合分析'
        })
    
    try:
        # 生成报告摘要
        report_summary = {
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'system': '沃土规划师 - Spark农业分析系统',
            'data_sources': 'MySQL数据库',
            'analysis_modules': ['气候趋势分析', '土壤分布分析', '作物适宜性分析', '区划优化建议']
        }
        
        # 统计信息
        statistics = {}
        if 'climate' in analysis_results:
            climate_data = analysis_results['climate']
            statistics['climate'] = {
                'temperature_records': len(climate_data['temperature_trend']),
                'precipitation_records': len(climate_data['precipitation_pattern']),
                'regional_zones': len(climate_data['regional_climate'])
            }
        
        if 'soil' in analysis_results:
            soil_data = analysis_results['soil']
            statistics['soil'] = {
                'soil_types': len(soil_data['soil_type_distribution']['soil_type'].unique()),
                'counties_analyzed': len(soil_data['county_soil_quality']),
                'ph_categories': len(soil_data['ph_distribution'])
            }
        
        if 'crop' in analysis_results:
            crop_data = analysis_results['crop']
            statistics['crop'] = {
                'crop_varieties': len(crop_data['crop_suitability_stats']['crop_name'].unique()),
                'suitable_areas': len(crop_data['best_planting_areas']),
                'optimization_zones': len(crop_data['zoning_optimization'])
            }
        
        return jsonify({
            'status': 'success',
            'report': {
                'summary': report_summary,
                'statistics': statistics
            }
        })
        
    except Exception as e:
        logger.error(f"❌ 导出报告失败: {e}")
        return jsonify({
            'status': 'error',
            'message': f'导出报告失败: {str(e)}'
        })

if __name__ == '__main__':
    print("🌱 沃土规划师 - Spark农业分析系统启动")
    print("=" * 60)
    print("🔗 访问地址: http://localhost:5003")
    print("📊 功能模块: Spark数据分析 + ECharts可视化")
    print("🗄️ 数据源: MySQL数据库")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5003, debug=True)
