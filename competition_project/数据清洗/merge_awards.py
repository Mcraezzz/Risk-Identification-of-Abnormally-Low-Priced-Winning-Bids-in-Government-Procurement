# -*- coding: utf-8 -*-
# 数据合并脚本：将ccgp_info_service_awards数据合并到supplier_credit并补全缺失字段
# 生成日期: 2026-05-10

import csv
import re
from openpyxl import load_workbook
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Province-level divisions
PROVINCE_NAMES = [
    '北京', '天津', '上海', '重庆',
    '河北', '山西', '辽宁', '吉林', '黑龙江',
    '江苏', '浙江', '安徽', '福建', '江西', '山东',
    '河南', '湖北', '湖南', '广东', '海南',
    '四川', '贵州', '云南', '陕西', '甘肃', '青海', '台湾',
    '内蒙古', '广西', '西藏', '宁夏', '新疆',
    '香港', '澳门'
]

CITY_TO_PROVINCE = {
    '石家庄': '河北', '太原': '山西', '沈阳': '辽宁', '长春': '吉林', '哈尔滨': '黑龙江',
    '南京': '江苏', '杭州': '浙江', '合肥': '安徽', '福州': '福建', '南昌': '江西', '济南': '山东',
    '郑州': '河南', '武汉': '湖北', '长沙': '湖南', '广州': '广东', '海口': '海南',
    '成都': '四川', '贵阳': '贵州', '昆明': '云南', '西安': '陕西', '兰州': '甘肃',
    '西宁': '青海', '台北': '台湾',
    '呼和浩特': '内蒙古', '南宁': '广西', '拉萨': '西藏', '银川': '宁夏', '乌鲁木齐': '新疆',
    '厦门': '福建', '宁波': '浙江', '青岛': '山东', '深圳': '广东', '大连': '辽宁',
    '苏州': '江苏', '无锡': '江苏', '常州': '江苏', '南通': '江苏', '徐州': '江苏',
    '扬州': '江苏', '镇江': '江苏', '泰州': '江苏', '盐城': '江苏', '淮安': '江苏',
    '连云港': '江苏', '宿迁': '江苏', '江阴': '江苏', '昆山': '江苏', '张家港': '江苏',
    '常熟': '江苏', '宜兴': '江苏', '溧阳': '江苏', '丹阳': '江苏', '扬中': '江苏',
    '句容': '江苏', '靖江': '江苏', '兴化': '江苏', '泰兴': '江苏', '如皋': '江苏',
    '海门': '江苏', '启东': '江苏', '如东': '江苏', '海安': '江苏', '东台': '江苏',
    '大丰': '江苏', '射阳': '江苏', '阜宁': '江苏', '滨海': '江苏', '响水': '江苏',
    '建湖': '江苏', '宝应': '江苏', '高邮': '江苏', '仪征': '江苏', '江都': '江苏',
    '邗江': '江苏', '广陵': '江苏', '通州': '江苏', '海陵': '江苏', '姜堰': '江苏',
    '珠海': '广东', '佛山': '广东', '东莞': '广东', '中山': '广东', '惠州': '广东',
    '江门': '广东', '汕头': '广东', '湛江': '广东', '肇庆': '广东', '茂名': '广东',
    '韶关': '广东', '梅州': '广东', '汕尾': '广东', '河源': '广东', '阳江': '广东',
    '清远': '广东', '潮州': '广东', '揭阳': '广东', '云浮': '广东', '台山': '广东',
    '开平': '广东', '鹤山': '广东', '恩平': '广东', '顺德': '广东', '南海': '广东',
    '温州': '浙江', '绍兴': '浙江', '嘉兴': '浙江', '湖州': '浙江', '金华': '浙江',
    '衢州': '浙江', '舟山': '浙江', '台州': '浙江', '丽水': '浙江', '温岭': '浙江',
    '乐清': '浙江', '瑞安': '浙江', '余姚': '浙江', '慈溪': '浙江', '海宁': '浙江',
    '平湖': '浙江', '桐乡': '浙江', '嘉善': '浙江', '海盐': '浙江', '德清': '浙江',
    '长兴': '浙江', '安吉': '浙江', '诸暨': '浙江', '嵊州': '浙江', '新昌': '浙江',
    '上虞': '浙江', '东阳': '浙江', '义乌': '浙江', '永康': '浙江', '兰溪': '浙江',
    '江山': '浙江', '龙游': '浙江', '常山': '浙江', '开化': '浙江', '岱山': '浙江',
    '嵊泗': '浙江', '龙泉': '浙江', '临海': '浙江', '玉环': '浙江', '三门': '浙江',
    '天台': '浙江', '仙居': '浙江', '奉化': '浙江', '宁海': '浙江', '象山': '浙江',
    '淳安': '浙江', '建德': '浙江', '桐庐': '浙江', '临安': '浙江', '富阳': '浙江',
    '萧山': '浙江', '余杭': '浙江',
    '淄博': '山东', '枣庄': '山东', '东营': '山东', '潍坊': '山东', '济宁': '山东',
    '泰安': '山东', '威海': '山东', '日照': '山东', '临沂': '山东', '德州': '山东',
    '聊城': '山东', '滨州': '山东', '菏泽': '山东', '烟台': '山东', '龙口': '山东',
    '莱阳': '山东', '莱州': '山东', '蓬莱': '山东', '招远': '山东', '栖霞': '山东',
    '海阳': '山东', '青州': '山东', '诸城': '山东', '寿光': '山东', '安丘': '山东',
    '高密': '山东', '昌邑': '山东', '曲阜': '山东', '邹城': '山东', '新泰': '山东',
    '肥城': '山东', '乳山': '山东', '荣成': '山东', '滕州': '山东', '乐陵': '山东',
    '禹城': '山东', '临清': '山东',
    '洛阳': '河南', '开封': '河南', '安阳': '河南', '鹤壁': '河南', '新乡': '河南',
    '焦作': '河南', '濮阳': '河南', '许昌': '河南', '漯河': '河南', '三门峡': '河南',
    '南阳': '河南', '商丘': '河南', '信阳': '河南', '周口': '河南', '驻马店': '河南',
    '济源': '河南',
    '襄阳': '湖北', '宜昌': '湖北', '黄石': '湖北', '十堰': '湖北', '荆州': '湖北',
    '荆门': '湖北', '鄂州': '湖北', '孝感': '湖北', '黄冈': '湖北', '咸宁': '湖北',
    '随州': '湖北', '恩施': '湖北', '仙桃': '湖北', '潜江': '湖北', '天门': '湖北',
    '神农架': '湖北',
    '株洲': '湖南', '湘潭': '湖南', '衡阳': '湖南', '邵阳': '湖南', '岳阳': '湖南',
    '常德': '湖南', '张家界': '湖南', '益阳': '湖南', '郴州': '湖南', '永州': '湖南',
    '怀化': '湖南', '娄底': '湖南', '湘西': '湖南',
    '桂林': '广西', '柳州': '广西', '梧州': '广西', '北海': '广西', '防城港': '广西',
    '钦州': '广西', '贵港': '广西', '玉林': '广西', '百色': '广西', '贺州': '广西',
    '河池': '广西', '来宾': '广西', '崇左': '广西',
    '三亚': '海南', '三沙': '海南', '儋州': '海南', '五指山': '海南', '琼海': '海南',
    '文昌': '海南', '万宁': '海南', '东方': '海南', '定安': '海南', '屯昌': '海南',
    '澄迈': '海南', '临高': '海南', '白沙': '海南', '昌江': '海南', '乐东': '海南',
    '陵水': '海南', '保亭': '海南', '琼中': '海南',
    '自贡': '四川', '攀枝花': '四川', '泸州': '四川', '德阳': '四川', '绵阳': '四川',
    '广元': '四川', '遂宁': '四川', '内江': '四川', '乐山': '四川', '南充': '四川',
    '眉山': '四川', '宜宾': '四川', '广安': '四川', '达州': '四川', '雅安': '四川',
    '巴中': '四川', '资阳': '四川', '阿坝': '四川', '甘孜': '四川', '凉山': '四川',
    '都江堰': '四川', '彭州': '四川', '邛崃': '四川', '崇州': '四川', '简阳': '四川',
    '遵义': '贵州', '六盘水': '贵州', '安顺': '贵州', '毕节': '贵州', '铜仁': '贵州',
    '黔西南': '贵州', '黔东南': '贵州', '黔南': '贵州',
    '曲靖': '云南', '玉溪': '云南', '保山': '云南', '昭通': '云南', '丽江': '云南',
    '普洱': '云南', '临沧': '云南', '楚雄': '云南', '红河': '云南', '文山': '云南',
    '西双版纳': '云南', '大理': '云南', '德宏': '云南', '怒江': '云南', '迪庆': '云南',
    '宝鸡': '陕西', '咸阳': '陕西', '铜川': '陕西', '渭南': '陕西', '延安': '陕西',
    '榆林': '陕西', '汉中': '陕西', '安康': '陕西', '商洛': '陕西',
    '嘉峪关': '甘肃', '金昌': '甘肃', '白银': '甘肃', '天水': '甘肃', '武威': '甘肃',
    '张掖': '甘肃', '平凉': '甘肃', '酒泉': '甘肃', '庆阳': '甘肃', '定西': '甘肃',
    '陇南': '甘肃', '临夏': '甘肃', '甘南': '甘肃',
    '石嘴山': '宁夏', '吴忠': '宁夏', '固原': '宁夏', '中卫': '宁夏',
    '克拉玛依': '新疆', '吐鲁番': '新疆', '哈密': '新疆', '昌吉': '新疆', '博尔塔拉': '新疆',
    '巴音郭楞': '新疆', '阿克苏': '新疆', '克孜勒苏': '新疆', '喀什': '新疆', '和田': '新疆',
    '伊犁': '新疆', '塔城': '新疆', '阿勒泰': '新疆', '石河子': '新疆', '阿拉尔': '新疆',
    '图木舒克': '新疆', '五家渠': '新疆', '北屯': '新疆', '铁门关': '新疆', '双河': '新疆',
    '可克达拉': '新疆', '昆玉': '新疆', '胡杨河': '新疆', '新星': '新疆',
    '唐山': '河北', '秦皇岛': '河北', '邯郸': '河北', '邢台': '河北', '保定': '河北',
    '张家口': '河北', '承德': '河北', '沧州': '河北', '廊坊': '河北', '衡水': '河北',
    '大同': '山西', '阳泉': '山西', '长治': '山西', '晋城': '山西', '朔州': '山西',
    '晋中': '山西', '运城': '山西', '忻州': '山西', '临汾': '山西', '吕梁': '山西',
    '鞍山': '辽宁', '抚顺': '辽宁', '本溪': '辽宁', '丹东': '辽宁', '锦州': '辽宁',
    '营口': '辽宁', '阜新': '辽宁', '辽阳': '辽宁', '盘锦': '辽宁', '铁岭': '辽宁',
    '朝阳': '辽宁', '葫芦岛': '辽宁',
    '吉林': '吉林', '四平': '吉林', '辽源': '吉林', '通化': '吉林', '白山': '吉林',
    '松原': '吉林', '白城': '吉林', '延边': '吉林', '长白山': '吉林',
    '齐齐哈尔': '黑龙江', '鸡西': '黑龙江', '鹤岗': '黑龙江', '双鸭山': '黑龙江',
    '大庆': '黑龙江', '伊春': '黑龙江', '佳木斯': '黑龙江', '七台河': '黑龙江',
    '牡丹江': '黑龙江', '黑河': '黑龙江', '绥化': '黑龙江', '大兴安岭': '黑龙江',
    '芜湖': '安徽', '蚌埠': '安徽', '淮南': '安徽', '马鞍山': '安徽', '淮北': '安徽',
    '铜陵': '安徽', '安庆': '安徽', '黄山': '安徽', '滁州': '安徽', '阜阳': '安徽',
    '宿州': '安徽', '六安': '安徽', '亳州': '安徽', '池州': '安徽', '宣城': '安徽',
    '景德镇': '江西', '萍乡': '江西', '九江': '江西', '新余': '江西', '鹰潭': '江西',
    '赣州': '江西', '吉安': '江西', '宜春': '江西', '抚州': '江西', '上饶': '江西',
}


def infer_province(text):
    if not text:
        return None
    for p in PROVINCE_NAMES:
        if p in text:
            return p
    for city, prov in CITY_TO_PROVINCE.items():
        if city in text:
            return prov
    return None


def infer_city(text, province):
    """Try to extract city from address text."""
    if not text:
        return None
    # Look for common city patterns: X省X市, X市X区
    # First try explicit city marker
    m = re.search(r'(\w+?)[市区县]', text)
    if m:
        city = m.group(1)
        # Validate it's a known city or at least 2 chars
        if len(city) >= 2:
            return city
    return None


def is_budget_missing(val):
    if val is None or str(val).strip() == '':
        return '是'
    try:
        v = float(val)
        if v == 0:
            return '是'
    except:
        return '是'
    return '否'


def main():
    excel_path = r'C:\Users\22672\Desktop\统计建模原数据\ccgp_merged_supplier_credit.xlsx'
    output_path = r'C:\Users\22672\Desktop\统计建模原数据\ccgp_merged_supplier_credit_merged.xlsx'
    csv_path = r'C:\Users\22672\Desktop\统计建模原数据\ccgp_info_service_awards(1).csv'

    # Load Excel
    print('加载 Excel...')
    wb = load_workbook(excel_path, data_only=True)
    ws = wb['合并表']
    headers = [cell.value for cell in next(ws.iter_rows(min_row=1, max_row=1))]
    existing_rows = list(ws.iter_rows(min_row=2, values_only=True))
    print(f'Excel 现有记录: {len(existing_rows)}')

    # Determine new ID start
    max_id = 0
    for row in existing_rows:
        try:
            vid = int(row[0])
            if vid > max_id:
                max_id = vid
        except:
            pass
    new_id_start = max_id + 1000
    print(f'新记录 ID 起始值: {new_id_start}')

    # Read CSV
    print('加载 CSV...')
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        csv_rows = list(reader)
    print(f'CSV 记录数: {len(csv_rows)}')

    # Field mapping: CSV field -> Excel field
    field_map = {
        'title': '公告标题',
        'url': '公告链接',
        'publish_date': '发布日期',
        'province': '项目省份',
        'city': '项目城市',
        'project_code': '项目编号',
        'project_name': '项目名称',
        'buyer_name': '采购人名称',
        'agency_name': '代理机构名称',
        'supplier_name': '原始供应商名称',
        'budget_amount': '预算金额',
        'winning_amount': '中标金额',
        'price_ratio': '中标/预算比例',
        'discount_rate': '节约率',
        'procurement_method': '采购方式',
        'service_period': '服务期限',
        'category': '服务类别',
        'announcement_text': '公告正文',
        'source': '公告来源',
    }

    # Build new rows
    new_rows = []
    for idx, csv_row in enumerate(csv_rows):
        new_id = new_id_start + idx
        row_data = {h: None for h in headers}
        row_data['记录ID'] = str(new_id)

        # Map known fields
        for csv_field, excel_field in field_map.items():
            row_data[excel_field] = csv_row.get(csv_field, '')

        # Fill missing fields
        supplier_name = csv_row.get('supplier_name', '')
        announcement_text = csv_row.get('announcement_text', '')
        proj_province = csv_row.get('province', '')

        # 统一供应商名称 = 原始供应商名称
        row_data['统一供应商名称'] = supplier_name

        # 统一社会信用代码 = empty
        row_data['统一社会信用代码'] = None

        # Infer supplier province
        supp_province = infer_province(supplier_name)
        if not supp_province and announcement_text:
            m = re.search(r'供应商地址[：:](.+)', announcement_text)
            if m:
                supp_province = infer_province(m.group(1))
        row_data['供应商所在省份'] = supp_province

        # Infer supplier city
        supp_city = None
        if announcement_text:
            m = re.search(r'供应商地址[：:](.+)', announcement_text)
            if m:
                supp_city = infer_city(m.group(1), supp_province)
        row_data['供应商所在城市'] = supp_city

        # 是否跨省中标
        if proj_province and supp_province:
            row_data['是否跨省中标'] = '是' if proj_province != supp_province else '否'
        else:
            row_data['是否跨省中标'] = None

        # 预算金额是否缺失
        row_data['预算金额是否缺失'] = is_budget_missing(csv_row.get('budget_amount'))

        # Order values by headers
        ordered = [row_data[h] for h in headers]
        new_rows.append(ordered)

    # Append to Excel
    print('追加数据到 Excel...')
    for row in new_rows:
        ws.append(row)

    # Save
    wb.save(output_path)
    print(f'保存完成。Excel 总记录数: {len(existing_rows) + len(new_rows)}')
    print(f'输出文件: {output_path}')
    print(f'新增记录数: {len(new_rows)}')

    # Stats
    cross = sum(1 for r in new_rows if r[headers.index('是否跨省中标')] == '是')
    same = sum(1 for r in new_rows if r[headers.index('是否跨省中标')] == '否')
    unknown = sum(1 for r in new_rows if r[headers.index('是否跨省中标')] is None)
    print(f'新增记录中 - 跨省中标: {cross}, 未跨省: {same}, 未知: {unknown}')


if __name__ == '__main__':
    main()
