# Rainforest API Reference

Base URL: `https://api.rainforestapi.com/request`

## Product Request

```
GET /request?api_key=KEY&type=product&asin=ASIN&amazon_domain=amazon.com
```

### Key Response Fields

| Path | 含义 |
|------|------|
| `product.asin` | ASIN |
| `product.title` | 商品标题 |
| `product.rating` | 评分（float） |
| `product.ratings_total` | 评论数 |
| `product.buybox_winner.price.raw` | 价格原始字符串（如 "$29.99"） |
| `product.buybox_winner.price.value` | 价格数值（float） |
| `product.buybox_winner.availability.raw` | 库存状态文本 |
| `product.bestsellers_rank[0].rank` | 主分类排名数字 |
| `product.bestsellers_rank[0].category` | 主分类名称 |

## Bestsellers Request

```
GET /request?api_key=KEY&type=bestsellers&url=CATEGORY_URL&amazon_domain=amazon.com
```

### Category URLs

| slug | URL |
|------|-----|
| all | https://www.amazon.com/Best-Sellers/zgbs |
| electronics | https://www.amazon.com/Best-Sellers/zgbs/electronics |
| books | https://www.amazon.com/Best-Sellers/zgbs/books |
| toys | https://www.amazon.com/Best-Sellers/zgbs/toys-and-games |
| kitchen | https://www.amazon.com/Best-Sellers/zgbs/kitchen |
| clothing | https://www.amazon.com/Best-Sellers/zgbs/apparel |
| sports | https://www.amazon.com/Best-Sellers/zgbs/sporting-goods |
| beauty | https://www.amazon.com/Best-Sellers/zgbs/beauty |
| home | https://www.amazon.com/Best-Sellers/zgbs/home-garden |

### Key Response Fields

| Path | 含义 |
|------|------|
| `bestsellers[].rank` | 榜单排名 |
| `bestsellers[].asin` | ASIN |
| `bestsellers[].title` | 商品名 |
| `bestsellers[].price.raw` | 价格字符串 |
| `bestsellers[].rating` | 评分 |
| `bestsellers[].ratings_total` | 评论数 |

## Error Codes

| HTTP 状态码 | 含义 | 处理方式 |
|-----------|------|---------|
| 200 | 成功 | 正常解析 |
| 401 | API Key 无效 | 报错，提示用户检查 Key |
| 429 | 超出限额 | 等待 60s 后降级爬取 |
| 5xx | 服务故障 | 立即降级爬取 |
