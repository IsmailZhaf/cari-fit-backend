from django.db import models
import re

class CV(models.Model):
    CATEGORY_CHOICES = [
        ('teknologi', 'Teknologi'),
        ('bisnis_manajemen', 'Bisnis dan Manajemen'),
        ('kreatif', 'Kreatif'),
        ('industri_manufaktur', 'Industri dan Manufaktur'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    user_id = models.CharField(max_length=255, unique=True)
    file_url = models.CharField(max_length=255)
    parsed_text = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Uncategorized')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(choices=STATUS_CHOICES, default='pending', max_length=20)

    def __str__(self):
        return f"CV {self.id} - {self.user_id}"
    
    def categorize_cv(self):
        if not self.parsed_text:
            return 'uncategorized'
        
        text_lower = self.parsed_text.lower()
        
        categories = {
            "teknologi": [
                "software engineer", "devops engineer", "data scientist",
                "cybersecurity analyst", "qa engineer", "ui/ux designer", "cloud engineer",
                "backend", "frontend", "full stack", "mobile developer", "machine learning", 
                "data analyst", "qa tester", "developer", "programmer", "python", "java", 
                "javascript", "react", "node.js", "database", "sql", "api"
            ],
            "bisnis_manajemen": [
                "business analyst", "project manager", "product manager",
                "hr specialist", "recruiter", "marketing specialist", "digital marketing",
                "finance analyst", "accountant", "manager", "analyst", "consultant",
                "coordinator", "supervisor", "leader", "management"
            ],
            "kreatif": [
                "graphic designer", "ui designer", "content writer", "copywriter",
                "video editor", "social media specialist", "brand strategist",
                "designer", "creative", "photoshop", "illustrator", "figma", "canva"
            ],
            "industri_manufaktur": [
                "mechanical engineer", "industrial engineer", "supply chain analyst",
                "procurement specialist", "quality assurance engineer", "qa manufaktur", 
                "qa logistik", "engineer", "manufacturing", "production", "operations",
                "logistics", "warehouse", "inventory"
            ]
        }
        
        # score keyword matches
        category_scores = {}
        for category, keywords in categories.items():
            score = 0
            for keyword in keywords:
                if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
                    score += 1
            category_scores[category] = score
        
        # find highest score
        if max(category_scores.values()) > 0:
            return max(category_scores, key=category_scores.get)
    
    def save(self, *args, **kwargs):
        if self.parsed_text and not kwargs.get('skip_categorization', False):
            self.category = self.categorize_cv()
        super().save(*args, **kwargs)