from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404
from django.urls import reverse
from .models import *
from django.http import Http404
import re
from bs4 import BeautifulSoup
from .utils import generateWebPageSchema

class HomePageView(TemplateView):
    template_name = "guides/home_page.html"
    extra_context = {}

    def get(self, *args, **kwargs):
        homepage_blog_obj = get_object_or_404(Blog, url_slug="guides",status="published")
        self.extra_context["homepage_blog_obj"] = homepage_blog_obj
        all_blogs = Blog.objects.filter(status="published").exclude(url_slug="guides").order_by("-updated_at")
        all_blogs_html_list = "<ul style='font-size: 1.1rem;'>"
        for blog in all_blogs:
            url = reverse("guides:blog_url",args=[blog.url_slug])
            all_blogs_html_list += f"<li><a href='{url}'>{blog.meta_title}</a></li>"
        all_blogs_html_list += "</ul>"
        self.extra_context["render_template_content_context"] = {"all_blogs_html_list":all_blogs_html_list}

        self.extra_context["meta_title"] = homepage_blog_obj.meta_title
        self.extra_context["meta_desc"] = homepage_blog_obj.meta_desc
        if homepage_blog_obj.featured_image:
            self.extra_context["meta_img_url"] = homepage_blog_obj.featured_image.url
        else:
            self.extra_context["meta_img_url"] = "/static/default_featured_image.jpg"
        return super().get(*args, **kwargs)


class BlogView(TemplateView):
    template_name = "guides/blog_page.html"
    extra_context = {}
    
    def getImg(self,soup):
        images = soup.select("img")        
        for img in images:
            if img.get("src"):
                img = img["src"]
                return img
        return None
    
    def getImgAlt(self,img_url):
        alt_text = None
        if img_url:
            img_url = img_url.split("/")[-1]
            alt_text = img_url.split(".")[0]
        return alt_text


    def get(self, *args, **kwargs):
        url_slug = kwargs.get("url_slug")
        if url_slug == "guides":
            raise Http404
        blog_obj = get_object_or_404(Blog, url_slug=url_slug,status="published")
        self.extra_context["blog_obj"] = blog_obj
        latest_blog_obj = Blog.objects.filter(status="published").exclude(url_slug="guides").order_by("-updated_at")[:10]
        latest_blogs = []
        for blog in latest_blog_obj:
            temp = {}
            content = blog.content
            soup = BeautifulSoup(content, 'html.parser')
            temp["title"] = blog.meta_title
            temp["img"] = self.getImg(soup)
            if not temp["img"] and blog.featured_image:
                temp["img"] = blog.featured_image.url
            temp["img_alt"] = self.getImgAlt(temp["img"])
            temp["link"] = reverse("guides:blog_url",args=[blog.url_slug])
            if temp["title"] and temp["img"]:
                latest_blogs.append(temp)
        self.extra_context["latest_blogs"] = latest_blogs
        
        url_prefix = f"{self.request.scheme}://{self.request.get_host()}"
        self.extra_context["meta_title"] = blog_obj.meta_title
        self.extra_context["meta_desc"] = blog_obj.meta_desc
        soup = BeautifulSoup(blog_obj.content, 'html.parser')
        first_img = self.getImg(soup)
        if blog_obj.featured_image:
            self.extra_context["meta_img_url"] = blog_obj.featured_image.url
        elif first_img:
            self.extra_context["meta_img_url"] = first_img
        else:
            self.extra_context["meta_img_url"] = "/static/default_featured_image.jpg"
        
        self.extra_context["web_page_schema"] = generateWebPageSchema(blog_obj,url_prefix)
        return super().get(*args, **kwargs)
