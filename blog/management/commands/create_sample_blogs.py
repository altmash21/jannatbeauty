from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from blog.models import BlogPost


class Command(BaseCommand):
    help = 'Create sample blog posts'

    def handle(self, *args, **kwargs):
        # Get or create a user for blog posts
        user, created = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@example.com', 'is_staff': True, 'is_superuser': True}
        )
        
        if created:
            user.set_password('admin')
            user.save()
            self.stdout.write(self.style.SUCCESS('Created admin user'))

        # Sample blog posts
        sample_posts = [
            {
                'title': 'The Importance of Daily Prayer in Islam',
                'content': '''Prayer (Salah) is one of the five pillars of Islam and is fundamental to a Muslim's faith and practice. 
                
It is a direct link between the worshipper and Allah. There is no intermediary between Allah and the worshipper, so through prayer, Muslims communicate directly with their Creator.

The five daily prayers are prescribed at specific times:
1. Fajr (Dawn Prayer)
2. Dhuhr (Noon Prayer)
3. Asr (Afternoon Prayer)
4. Maghrib (Sunset Prayer)
5. Isha (Night Prayer)

Each prayer takes only a few minutes to perform, yet the spiritual benefits are immense. Prayer helps Muslims maintain God-consciousness throughout the day, provides peace and tranquility, and serves as a constant reminder of our purpose in life.

Regular prayer also brings discipline to one's life, teaches patience and perseverance, and strengthens the bond between the individual and their community through congregational prayers.''',
                'category': 'Worship',
            },
            {
                'title': 'Understanding the Quran: A Guide for Beginners',
                'content': '''The Quran is the holy book of Islam, revealed to Prophet Muhammad (peace be upon him) over a period of 23 years. It is the literal word of Allah and serves as the primary source of Islamic teachings and laws.

For beginners looking to understand the Quran, here are some important points:

**Start with Translation**: Begin by reading a good translation in your native language. While Arabic is the original language, translations help non-Arabic speakers understand the message.

**Learn Basic Context**: Understanding the historical context (Tafsir) of verses helps in comprehending their meanings and applications.

**Consistent Reading**: Set aside time daily for Quranic recitation and reflection, even if it's just a few verses.

**Seek Knowledge**: Join study circles or classes where you can learn with others and ask questions.

**Reflect and Apply**: The Quran is not just for reading; it's a guide for life. Reflect on how the verses apply to your daily life.

Remember, the journey of understanding the Quran is lifelong, and every step brings you closer to Allah.''',
                'category': 'Education',
            },
            {
                'title': 'Ramadan: The Blessed Month of Fasting',
                'content': '''Ramadan is the ninth month of the Islamic calendar and is observed by Muslims worldwide as a month of fasting, prayer, reflection, and community.

**What is Fasting?**
During Ramadan, Muslims fast from dawn to sunset, abstaining from food, drink, and other physical needs. This practice teaches self-discipline, self-control, and sympathy for those less fortunate.

**Spiritual Benefits:**
- Increased devotion and God-consciousness
- Opportunity to seek forgiveness and cleanse the soul
- Development of patience and willpower
- Enhanced empathy for the poor and hungry

**Community and Charity:**
Ramadan strengthens community bonds through:
- Iftar gatherings (breaking fast together)
- Taraweeh prayers at the mosque
- Increased charitable giving (Zakat and Sadaqah)

**Night of Power (Laylat al-Qadr):**
The last ten nights of Ramadan include Laylat al-Qadr, believed to be better than a thousand months. Muslims spend these nights in intense worship and supplication.

The month concludes with Eid al-Fitr, a joyous celebration marking the end of fasting.''',
                'category': 'Ramadan',
            },
            {
                'title': 'Hajj: The Sacred Pilgrimage to Mecca',
                'content': '''Hajj is the annual Islamic pilgrimage to Mecca, Saudi Arabia, and is mandatory for all able-bodied Muslims who can afford it at least once in their lifetime.

**The Five Pillars Connection:**
Hajj is the fifth pillar of Islam, demonstrating the unity of Muslims worldwide as they gather to worship Allah at the holiest site in Islam.

**The Journey:**
Hajj takes place during the Islamic month of Dhul Hijjah and involves several rituals:

1. **Ihram**: Pilgrims enter a state of spiritual purity by wearing simple white garments
2. **Tawaf**: Circling the Kaaba seven times
3. **Sa'i**: Walking seven times between the hills of Safa and Marwah
4. **Day of Arafah**: Standing in prayer and supplication on Mount Arafah
5. **Muzdalifah**: Collecting pebbles for the stoning ritual
6. **Stoning of the Devil**: Symbolically rejecting evil
7. **Sacrifice**: Commemorating Prophet Ibrahim's willingness to sacrifice his son

**Spiritual Transformation:**
Hajj is a profound spiritual experience that:
- Wipes away sins
- Promotes equality (all pilgrims wear the same simple clothing)
- Strengthens faith and devotion
- Creates a sense of global Muslim unity

Many pilgrims describe Hajj as life-changing, returning home with renewed faith and purpose.''',
                'category': 'Pilgrimage',
            },
            {
                'title': 'Islamic Art and Calligraphy: Beauty in Faith',
                'content': '''Islamic art and calligraphy represent a unique and beautiful expression of faith, culture, and creativity that has developed over centuries.

**The Essence of Islamic Art:**
Islamic art is characterized by:
- Geometric patterns symbolizing the infinite nature of Allah
- Arabesque designs featuring intricate, repeating patterns
- Avoidance of representational imagery in religious contexts
- Focus on abstract forms and calligraphy

**Islamic Calligraphy:**
Arabic calligraphy is perhaps the most revered art form in Islamic culture. The written word, especially verses from the Quran, is considered sacred and is beautifully rendered in various styles:

- **Kufic**: One of the oldest forms, angular and geometric
- **Naskh**: Clear and legible, commonly used for Quranic texts
- **Thuluth**: Elegant and curved, often used for decorative purposes
- **Diwani**: Ornate style developed in the Ottoman court

**Applications:**
Islamic art and calligraphy beautify:
- Mosques and Islamic architecture
- Quranic manuscripts
- Decorative items for homes
- Personal accessories and jewelry

**Modern Relevance:**
Today, Islamic art continues to inspire:
- Contemporary artists worldwide
- Interior design trends
- Fashion and textile design
- Digital art and graphics

Through Islamic art, Muslims express their faith aesthetically while creating beauty that inspires contemplation and remembrance of Allah.''',
                'category': 'Culture',
            },
            {
                'title': 'Teaching Islamic Values to Children',
                'content': '''Raising children with strong Islamic values is one of the most important responsibilities for Muslim parents. Here's a comprehensive guide to help instill faith and values in young hearts.

**Start Early:**
Begin teaching Islamic concepts from an early age through:
- Reading children's Islamic books
- Playing Islamic songs and nasheeds
- Using Islamic toys and educational materials
- Telling stories of Prophets and righteous people

**Lead by Example:**
Children learn best through observation:
- Pray regularly in front of them
- Read Quran daily
- Show good character and manners
- Treat others with kindness and respect

**Make Learning Fun:**
Engage children through:
- Islamic apps and games
- Quran memorization competitions
- Mosque activities and Islamic schools
- Arts and crafts with Islamic themes

**Core Values to Teach:**
1. **Aqeedah**: Understanding Allah and the basics of faith
2. **Salah**: Regular prayer from a young age
3. **Akhlaq**: Good character, honesty, and kindness
4. **Respect**: For parents, elders, and all of Allah's creation
5. **Gratitude**: Being thankful to Allah for all blessings

**Create Islamic Environment:**
- Decorate with Islamic art and calligraphy
- Keep Islamic books accessible
- Establish family prayer times
- Celebrate Islamic occasions

**Be Patient and Consistent:**
Remember that character building is a gradual process. Be patient, make du'a for your children, and trust in Allah's guidance.

The Prophet (peace be upon him) said: "Each of you is a shepherd and each of you is responsible for his flock."''',
                'category': 'Family',
            },
        ]

        created_count = 0
        for post_data in sample_posts:
            post, created = BlogPost.objects.get_or_create(
                title=post_data['title'],
                defaults={
                    'author': user,
                    'content': post_data['content'],
                    'category': post_data['category'],
                    'published': True,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created blog post: {post.title}'))

        if created_count > 0:
            self.stdout.write(self.style.SUCCESS(f'\nSuccessfully created {created_count} blog posts!'))
        else:
            self.stdout.write(self.style.WARNING('All sample blog posts already exist.'))
