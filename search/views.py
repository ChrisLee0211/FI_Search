import json
from datetime import datetime

from django.shortcuts import render
from django.views.generic.base import View
from django.shortcuts import HttpResponse
from elasticsearch import Elasticsearch
import redis

from search.models import JobboleEsType, ZhihuQuestionEsType
# Create your views here.
client = Elasticsearch(hosts=['127.0.0.1'])  # 初始化一个es的连接
redis_cli = redis_cli = redis.StrictRedis(host="localhost", charset="UTF-8", decode_responses=True)  # 初始化一个redis连接


class IndexView(View):
    def get(self, request):
        top_search = redis_cli.zrevrangebyscore("search_keyword_set", "+inf", "-inf", start=0, num=5)
        return render(request, "index.html", {"top_search": top_search})


class SearchSuggest(View):
    """
    搜索建议显示逻辑
    """
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


class SearchView(View):
    """
    搜索详情页
    """

    def get(self, request):
        key_words = request.GET.get('q', '')
        redis_cli.zincrby(name="search_keyword_set", value=key_words, amount=1)  # 利用redis建立一个有序集合，将热门搜索词放进去，每次搜索就+1
        top_search = redis_cli.zrevrangebyscore("search_keyword_set", "+inf", "-inf", start=0, num=5)
        jobbole_count = int(client.count(index="jobbole")["count"])
        zhihu_count = int(client.count(index="zhihu", doc_type="question")["count"])
        key_type = request.GET.get('s_type', '')
        page = request.GET.get("p", "")
        try:
            page = int(page)
        except:
            page = 1
        start_time = datetime.now()
        if key_type == "article":
            response = client.search(
                index="jobbole",
                body={
                    'query': {
                        "multi_match": {
                            "query": key_words,
                            "fields": ["title", "content", "tag"]
                        }
                    },
                    "from": (page - 1) * 10,
                    "size": 10,
                    "highlight": {  # 词语高亮
                                    "pre_tags": ["<span class='keyWord'>"],
                                    "post_tags": ["</span>"],
                                    "fields": {
                                        "title": {},
                                        "content": {}
                                    }
                                    }
                }
            )
            total_nums = response["hits"]["total"]
            if (page % 10) > 0:  # 总页数
                page_nums = int(total_nums / 10) + 1
            else:
                page_nums = int(total_nums / 10)
        if key_type == "question":
            response = client.search(
                index="zhihu",
                doc_type="question",
                body={
                    'query': {
                        "multi_match": {
                            "query": key_words,
                            "fields": ["title", "content"]
                        }
                    },
                    "from": (page - 1) * 10,
                    "size": 10,
                    "highlight": {  # 词语高亮
                                    "pre_tags": ["<span class='keyWord'>"],
                                    "post_tags": ["</span>"],
                                    "fields": {
                                        "title": {},
                                        "content": {}
                                    }
                                    }
                }
            )
            total_nums = response["hits"]["total"]
            if (page % 10) > 0:  # 总页数
                page_nums = int(total_nums / 10) + 1
            else:
                page_nums = int(total_nums / 10)
        end_time = datetime.now()
        used_second = (end_time - start_time).total_seconds()
        hit_list = []
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
        return render(request, "result.html", {"all_list": hit_list,
                                               "key_words": key_words,
                                               "total_nums": total_nums,
                                               "page_nums": page_nums,
                                               "used_second": used_second,
                                               "page": page,
                                               "jobbole_count": jobbole_count,
                                               "zhihu_count": zhihu_count,
                                               "top_search": top_search})



