# 爬虫提示词

> 任何 AI 可直接调用以下命令抓取实习数据（多站点）

## 站点抓取（直接入库）

```
cd server/scrapers

python scraper.py --site nowcoder   # 牛客汇总（列表页收集链接→详情页）
python scrape_meituan.py            # 美团（公开 API）
python scrape_alibaba.py            # 阿里（XSRF-TOKEN + batchId）
python scrape_xiaohongshu.py        # 小红书（SPA 宿主免鉴权 API）
python scrape_tencent.py            # 腾讯（searchPosition 分页）
python scrape_huawei.py             # 华为（session + Referer，jobType=3）
python scrape_bytedance.py          # 字节（API + CSRF token）
```

## 数据推送后台（联动）

```
# 把 parsed JSON 导出为标准 CSV
python export_and_push.py

# 导出并直接推送到后台导入接口（需后端已启动）
python export_and_push.py --push
```

## 大厂整页分割

```
python segment_company.py   # 字节整页文本按「职位ID」边界分割入库
```

## 配置说明

- `sites/nowcoder.py` — 牛客配置
- `sites/default_site.py` — 大厂通用（整页→AI 分割）
- `extract.py` — 详情页「职位描述/任职要求」边界分割（split_detail）
- `config.py` — 站点列表、公司名兜底提取、分类规则

各站 API 逆向参考：github.com/HA7CH/job-pro（meituan/alibaba/huawei/xiaohongshu/tencent/bytedance .ts）

## 数据库连接

```
MySQL: localhost:3306 / internship_platform / root / 200619 / utf8mb4
```

## 牛客网URL规则

```
列表页: https://www.nowcoder.com/jobs/intern/center?recruitType=2&city=北京
详情页: https://www.nowcoder.com/jobs/detail/{jobId}
```

## 待优化

- 牛客「去官网投」类岗位真实雇主未知（company 标记为「待识别」）
- 华为校招淡季岗位极少（jobType=3 仅个位数，季节开放后自动增多）
- 各公司 API 接口可能变更，需按需维护（字节已适配 CSRF token）
