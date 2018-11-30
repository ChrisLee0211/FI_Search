# FI_Search
一个基于elasticsearch开发的搜索引擎网站

## 项目介绍
是一个通过用`scrapy`爬取知乎和伯乐在线内容作为数据，用`elasticsearch`作为搜索引擎，以`django`为基础搭建的搜索网站，实现了搜索即时建议、热门搜索排名、搜索条目展示、模糊分词匹配、分词高亮等功能

## 开发工具
> Django==2.0\
elasticsearch==5.5.3\
elasticsearch-dsl==5.2.0\
pytz==2018.7\
redis==3.0.1\
six==1.11.0\
urllib3==1.24.1

备注：具体如何用scrapy爬取知乎全网和伯乐在线，请参考本人另一个仓库里的项目代码（集成了随机代理IP，UA，selenium模拟登陆绕过验证等功能）传送门：[zhihu&jobbole](https://github.com/ChrisLee0211/elasticsearch-in-scrapy)

## 功能实现说明：

## 效果演示：![example](https://github.com/ChrisLee0211/FI_Search/blob/master/static/img/example01.gif)
1. 搜索建议功能：\
  首先运用了 _elasticsearch_ 作为 _django_ 的model层，在设计索引时加入```suggest```字段，以`ik_max_word`作为中文分词分析器，随后在`view`中通过HTTP中的get方法获取到url中的`keyword`，然后根据搜索类型连接 _elasticsearch_ 返回一个搜索建议列表，再返回前端渲染;部分代码如下：
  ```python
  def get(self, request):
        key_words = request.GET.get('s', '')  # 接收一个s变量，s包含了输入框的词，以此返回给elasticsearch做分词匹配
        key_type = request.GET.get("s_type", "")
        if key_type == "article":
            re_words = []
            if key_words:
                s = JobboleEsType.search()
                s = s.suggest('my_suggest_jobbole', key_words, completion={
                    "field": "suggest", "fuzzy": {
                        "fuzziness": 2
                    },
                    "size": 5
                })
                suggestions = s.execute_suggest()  # 返回一个建议词组列表
                for match in suggestions.my_suggest_jobbole[0].options:
                    source = match._source
                    result = source["title"]
                    re_words.append(result)
        if key_type == "question":
            re_words = []
            if key_words:
                s = ZhihuQuestionEsType.search()
                s = s.suggest('my_suggest_zhihu', key_words, completion={
                    "field": "suggest", "fuzzy": {
                        "fuzziness": 2
                    },
                    "size": 5
                })
                suggestions = s.execute_suggest()  # 返回一个建议词组列表
                for match in suggestions.my_suggest_zhihu[0].options:
                    source = match._source
                    result = source["title"]
                    re_words.append(result)

        return HttpResponse(json.dumps(re_words), content_type="application/json")
  ```
  
2. 热门搜索排名：\
  这里采用了`redis`自带的有序集合方法```zincrby()```，每次输入关键字进行搜索，就会在有序集合里创建相应的string，然后获取一次就+1，形成排名，当取出排名时则用redis的```zrevrangebyscore()```方法对有序集合进行分数排序取出，部分代码如下：
  ```python
  redis_cli = redis_cli = redis.StrictRedis(host="localhost", charset="UTF-8", decode_responses=True)  # 初始化一个redis连接
  redis_cli.zincrby(name="search_keyword_set", value=key_words, amount=1)  # 利用redis建立一个有序集合，将热门搜索词放进去，每次搜索就+1
  top_search = redis_cli.zrevrangebyscore("search_keyword_set", "+inf", "-inf", start=0, num=5)
  ```
  因为`redis`的持久化特点，以及支持多种数据类型的存储，非常适合存储类似搜索字段中混合字符的数据。
  
3. 搜索匹配功能：\
  运用了 _elasticsearch_ 中的`multi-match`功能，对内容的title、content、tag进行分词匹配，权重是title>tag>content。\
  实现原理是，运用了 _elasticsearch_ 库底层的`search`接口，编写es本身的搜索语句来获取到一个包含了结果的dict，然后通过[`kibana插件`](https://www.elastic.co/cn/products/kibana)分别查看结果的dict结构，在 _django_ 中一一映射成一个列表，返回到前端渲染。部分代码：
  ```python
  for hit in response['hits']['hits']:
      hit_dict = {}
      if "title" in hit["highlight"]:
          hit_dict["title"] = "".join(hit["highlight"]["title"])
      else:
          hit_dict["title"] = hit["_source"]["title"]
      if "content" in hit["highlight"]:
          hit_dict["content"] = "".join(hit["highlight"]["content"])[:400]
      else:
          hit_dict["content"] = hit["_source"]["content"][:400]
      if key_type == "article":
          hit_dict["create_date"] = hit["_source"]["create_date"]
      else:
          hit_dict["create_date"] = hit["_source"]["crawl_time"]
      hit_dict["score"] = hit["_score"]
      hit_dict["url"] = hit["_source"]["url"]
      hit_list.append(hit_dict)
  ```
## 收获：
1. 单单作为数据库的话，elasticsearch和mysql、MongoDB各有特色，最大的感受是，在开发工作平台类、模块关系复杂型的项目比较适合用 _mysql_ ，如果是大数据量存储，但是查询事务不复杂的话适合用 _mongodb_ ，而 _elasticsearch_ 其实核心是搜索引擎。
2. 学习到了分布式爬虫系统的开发，使用redis队列能高效完成爬取量庞大的任务，并且持久化的特点可以使得scrapy随停随开；
3. 加深了对浏览器发送请求、接收请求、HTTP协议的认识，对反爬虫、反反爬虫有了进一步的了解
