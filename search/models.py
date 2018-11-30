from django.db import models

# Create your models here.
from datetime import datetime
from elasticsearch_dsl import DocType, Date, Nested, Boolean, \
    analyzer, Completion, Keyword, Text, Integer
from elasticsearch_dsl.analysis import CustomAnalyzer as _CustomAnalyzer

from elasticsearch_dsl.connections import connections

connections.create_connection(hosts=["localhost"])


class CustomAnalyzer(_CustomAnalyzer):
    # ��д�Զ��������
    def get_analysis_definition(self):
        return {}


ik_analyzer = CustomAnalyzer("ik_max_word", filter=["lowercase"])  # ����filter���д�Сд�Զ�ת��


class JobboleEsType(DocType):
    suggest = Completion(analyzer=ik_analyzer)  # ע�⣬elasticsearch_dsl��Դ���Completionû����analyzer��ѡ��֧�֣���Ҫ��ik�Զ����ȥ
    title = Text(analyzer="ik_max_word")
    create_date = Date()
    url = Keyword()
    url_object_id = Keyword()
    front_image_url = Keyword()
    front_image_path = Keyword()
    praise_nums = Integer()
    comment_nums = Integer()
    fav_nums = Integer()
    content = Text(analyzer="ik_max_word")
    tag = Text(analyzer="ik_max_word")

    class Meta:
        index = "jobbole"
        doc_type = "article"


class ZhihuQuestionEsType(DocType):
    zhihu_id = Integer()
    topics = Keyword()
    url = Keyword()
    title = Text(analyzer="ik_max_word")
    content = Text(analyzer="ik_max_word")
    answer_num = Integer()
    comments_num = Integer()
    watch_user_num = Integer()
    click_num = Integer()
    crawl_time = Date()

    class Meta:
        index = "zhihu"
        doc_type = "question"


class ZhihuAnwserEsType(DocType):
    zhihu_id = Integer()
    url = Keyword()
    question_id = Integer()
    author_id = Integer()
    content = Text(analyzer="ik_max_word")
    praise_num = Integer()
    comments_num = Integer()
    create_time = Date()
    update_time = Date()
    crawl_time = Date()

    class Meta:
        index = "zhihu"
        doc_type = "answer"


if __name__ == "__main__":
    # ZhihuAnwserEsType.init()
    # ZhihuQuestionEsType.init()
    JobboleEsType.init()
