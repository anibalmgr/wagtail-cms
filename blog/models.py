from dataclasses import Field
from django.db import models
from pyexpat import model
from django import forms
from modelcluster.fields import ParentalKey
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase
from wagtail.core.models import Page, Orderable
from wagtail.core.fields import RichTextField
from wagtail.admin.edit_handlers import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.search import index
from wagtail.snippets.models import register_snippet
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.snippets.edit_handlers import SnippetChooserPanel

from modelcluster.fields import ParentalKey, ParentalManyToManyField
from taggit.models import TaggedItemBase


class BlogIndexPage(Page):
    intro = RichTextField(blank=True)

    def get_context(self, request):
        # Update context to include only published posts, ordered by reverse-chron
        context = super().get_context(request)
        blogpages = self.get_children().live().order_by('-first_published_at')
        context['blogpages'] = blogpages
        return context


class BlogPageTag(TaggedItemBase):
    content_object = ParentalKey(
        'BlogPage',
        related_name='tagged_items',
        on_delete=models.CASCADE
    )


class BlogPage(Page):
    date = models.DateField("Post date")
    intro = models.CharField(max_length=250)
    body = RichTextField(blank=True)
    authors = ParentalManyToManyField('blog.BlogAuthor', blank=True)
    tags = ClusterTaggableManager(through=BlogPageTag, blank=True)
    categories = ParentalManyToManyField('blog.BlogCategory', blank=True)

    def main_image(self):
        gallery_item = self.gallery_images.first()
        if gallery_item:
            return gallery_item.image
        else:
            return None

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
    ]

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('authors', widget=forms.CheckboxSelectMultiple),
            FieldPanel('date'),
            FieldPanel('tags'),
            FieldPanel('categories', widget=forms.CheckboxSelectMultiple),
        ], heading="Blog information"),
        FieldPanel('intro'),
        FieldPanel('body', classname="full"),
        InlinePanel('gallery_images', label="Gallery images"),
    ]


class BlogPageGalleryImage(Orderable):
    page = ParentalKey(BlogPage, on_delete=models.CASCADE,
                       related_name='gallery_images')
    image = models.ForeignKey(
        'wagtailimages.Image', on_delete=models.CASCADE, related_name='+'
    )
    caption = models.CharField(blank=True, max_length=250)

    panels = [
        ImageChooserPanel('image'),
        FieldPanel('caption'),
    ]


class BlogTagIndexPage(Page):

    def get_context(self, request):

        # Filter by tag
        tag = request.GET.get('tag')
        blogpages = BlogPage.objects.filter(tags__name=tag)

        # Update template context
        context = super().get_context(request)
        context['blogpages'] = blogpages
        return context


class BlogAuthorsOrderable(Orderable):
    """This allows us to select one or more blog authors from Snippets."""

    page = ParentalKey(BlogPage, related_name="blog_authors")
    author = models.ForeignKey(
        "blog.BlogAuthor",
        on_delete=models.CASCADE,
    )

    panels = [
        # Use a SnippetChooserPanel because blog.BlogAuthor is registered as a snippet
        SnippetChooserPanel("author"),
    ]


@register_snippet
class BlogCategory(models.Model):
    name = models.CharField(max_length=300)
    icon = models.ForeignKey(
        'wagtailimages.Image', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+'
    )

    panels = [
        ImageChooserPanel('icon'),
        FieldPanel('name'),
    ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'blog categories'


@register_snippet
class BlogAuthor(models.Model):
    """Blog author"""

    username = models.CharField(max_length=50)
    avatar = models.ForeignKey("wagtailimages.Image",
                               on_delete=models.SET_NULL,
                               null=True,
                               blank=False,
                               related_name="+",)
    role = models.CharField(max_length=50)

    panels = [
        FieldPanel('username'),
        FieldPanel('role'),
        ImageChooserPanel('avatar')
    ]

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = "Author"
        verbose_name_plural = 'Authors'
