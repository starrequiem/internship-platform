"""
Target site configs + classification rules
"""

SITES = [
    {
        'name': 'Huawei',
        'url': 'https://career.huawei.com/reccampportal/portal5/campus-recruitment.html',
        'type': 'company', 'fetcher': 'dynamic',
        'selectors': {
            'list': '.position-list li, .job-item, .recruit-list-item',
            'title': '.job-title, .position-name, h3',
            'city': '.job-city, .work-place, .location',
            'job_type': '.job-type, .position-type',
            'description': '.job-desc, .position-desc',
        },
        'parser': 'html',
    },
    {
        'name': 'Tencent',
        'url': 'https://join.qq.com/post.html',
        'type': 'company', 'fetcher': 'dynamic',
        'selectors': {
            'list': '.post-list li, .job-card, .position-item',
            'title': '.post-name, .job-name, .title',
            'city': '.post-location, .work-city, .location',
            'job_type': '.post-type, .category',
            'description': '.post-desc, .job-requirement',
        },
        'parser': 'html',
    },
    {
        'name': 'ByteDance',
        'url': 'https://jobs.bytedance.com/campus/position',
        'type': 'company', 'fetcher': 'dynamic',
        'selectors': {
            'list': '.position-list-wrapper > div, .job-card, [class*="position"]',
            'title': '.position-title, .job-title, [class*="title"]',
            'city': '.position-location, .city, [class*="location"]',
            'job_type': '.position-category, .category, [class*="category"]',
            'description': '.position-desc, [class*="desc"]',
        },
        'parser': 'html',
    },
    {
        'name': 'Alibaba',
        'url': 'https://talent.alibaba.com/campus/position-list',
        'type': 'company', 'fetcher': 'dynamic',
        'selectors': {
            'list': '.position-list li, .job-item, [class*="position"]',
            'title': '.position-name, .job-title',
            'city': '.work-location, .city',
            'job_type': '.position-direction, .category',
            'description': '.position-description',
        },
        'parser': 'html',
    },
    {
        'name': 'Meituan',
        'url': 'https://zhaopin.meituan.com/web/campus',
        'type': 'company', 'fetcher': 'dynamic',
        'selectors': {
            'list': '.job-list li, .position-card, [class*="job"]',
            'title': '.job-name, .position-title',
            'city': '.job-city, .work-place',
            'job_type': '.job-category, .type',
            'description': '.job-desc',
        },
        'parser': 'html',
    },
    {
        'name': 'Xiaohongshu',
        'url': 'https://job.xiaohongshu.com/campus',
        'type': 'company', 'fetcher': 'dynamic',
        'selectors': {
            'list': '.job-list li, .position-item',
            'title': '.job-name, .title',
            'city': '.job-location, .city',
            'job_type': '.job-type, .category',
            'description': '.job-desc',
        },
        'parser': 'html',
    },
    {
        'name': 'Shixiseng',
        'url': 'https://www.shixiseng.com/interns',
        'type': 'third_party', 'fetcher': 'stealthy',
        'selectors': {
            'list': '.interns-list .intern-wrap, .position-item',
            'title': '.intern-title, .job-name, h3 a',
            'company': '.company-name, .intern-company',
            'city': '.city, .work-place',
            'salary': '.salary, .day-money',
            'description': '.job-desc, .intern-detail',
        },
        'parser': 'html',
    },
    {
        'name': 'Nowcoder',
        'url': 'https://www.nowcoder.com/intern/center',
        'type': 'third_party', 'fetcher': 'dynamic',
        'selectors': {
            'list': '.intern-list li, .recruit-item',
            'title': '.recruit-title, .job-name',
            'company': '.company-name, .recruit-company',
            'city': '.city, .location',
            'salary': '.salary, .pay',
            'description': '.recruit-desc, .job-desc',
        },
        'parser': 'html',
    },
    {
        'name': 'XYBSYW',
        'url': 'https://m.xybsyw.com/page/student.html',
        'type': 'third_party', 'fetcher': 'stealthy',
        'selectors': {},
        'parser': 'fulltext',
    },
]

CLASSIFY_RULES = {
    'job_type': {
        '技术开发': ['前端','后端','Java','Python','Go','C++','开发','Web','全栈','Android','iOS','客户端','服务端',
                    'Golang','React','Vue','Node','工程师','程序员','软件','测试','运维','SRE','安全','架构'],
        '产品经理': ['产品经理','产品助理','PM','Product'],
        'UI/UX 设计': ['UI','UX','交互设计','视觉设计','GUI','设计'],
        '数据分析': ['数据分析','数据科学','BI','商业分析','分析师','大数据','ETL'],
        '算法/AI': ['算法','机器学习','深度学习','AI','NLP','CV','大模型','LLM','人工智能','AIGC'],
        '运营': ['运营','内容','新媒体','社群','电商','活动','用户'],
        '市场商务': ['市场','营销','商务','销售','品牌','PR','公关','拓展','客户'],
        '人力资源': ['HR','人力','招聘','组织','培训','员工'],
        '财务会计': ['财务','会计','审计','税务','出纳','金融'],
        '硬件芯片': ['硬件','芯片','IC','FPGA','嵌入式','射频','电子','半导体'],
        '职能支持': ['行政','法务','合规','采购','供应链','物流','翻译','助理'],
    },
    'education': {
        '博士': ['博士','PhD','博士研究生'],
        '硕士及以上': ['硕士及以上','硕士研究生','硕士以上'],
        '本科及以上': ['本科及以上','本科以上','本科或以上','本科'],
        '不限': ['不限','学历不限'],
    },
}

CITIES = [
    '北京','上海','广州','深圳','杭州','成都','南京','武汉',
    '西安','苏州','重庆','天津','长沙','郑州','合肥','厦门',
    '远程','Remote',
]

COMPANIES = [
    '字节跳动','腾讯','阿里巴巴','美团','华为','百度','京东',
    '小红书','快手','网易','滴滴','哔哩哔哩','拼多多',
    '蔚来','理想汽车','小鹏汽车','小米','大疆','微软','Google',
    '亚马逊','Apple','英伟达','NVIDIA','特斯拉','蚂蚁集团',
    'Shopee','Lazada','Zoom','Oracle','SAP','IBM','Intel',
    '携程','商汤','旷视','地平线','寒武纪','中兴','联想',
    'OPPO','vivo','荣耀','海康威视','大华','新浪','搜狐',
    '360','知乎','唯品会','得物','米哈游','莉莉丝','叠纸',
]
