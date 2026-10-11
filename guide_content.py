"""راهنمای داخلی برنامه به دو زبان. ساختار هر دو زبان باید یکسان باشد."""

GUIDE = {
    'fa': [
        {
            'title': 'این برنامه چه کاری می‌کند',
            'blocks': [
                ('p', 'ProtonVPN Scanner فهرست سرورهای ProtonVPN را می‌گیرد، سرعت هر سرور را می‌سنجد و سریع‌ترین‌ها را اول نشان می‌دهد.'),
                ('p', 'سرعت با پینگ (ping) سنجیده می‌شود. پینگ یعنی زمانی که یک پیام کوچک لازم دارد تا به سرور برسد و برگردد. این زمان بر حسب میلی‌ثانیه (ms) است و هرچه عدد کمتر باشد، سرور سریع‌تر است.'),
                ('p', 'برنامه برای سرورهای پیداشده، کانفیگ WireGuard هم می‌سازد. کانفیگ (config) یک فایل تنظیمات است که برنامه‌ی WireGuard آن را می‌خواند تا به سرور وصل شود.'),
                ('p', 'سروری که «سالم» نشان داده می‌شود فقط از آزمون پینگ اولیه گذشته است. برای اطمینان، آن را در یک کلاینت واقعی تست کنید؛ بخش «تست واقعی با یک کلاینت» را ببینید.'),
                ('ul', [
                    'فهرست سرورها را بارگذاری کنید. به این فهرست «دیتابیس» (database) می‌گویند.',
                    'نوع سرور را انتخاب کنید: «رایگان» (Free)، «پولی» (Premium) یا «همه» (All). در صورت نیاز، قاره و کشور را هم انتخاب کنید.',
                    'اسکن را شروع کنید تا سرورهای فعال، یعنی سرورهایی که پاسخ می‌دهند، پیدا شوند.',
                    'IP سرور (یعنی آدرس عددی آن) را کپی کنید، یا کانفیگ آن را کپی یا به‌صورت فایل ذخیره کنید.',
                ]),
                ('p', 'این راهنما در تب «راهنما» (Guide) است. زبان برنامه (English یا فارسی) را در تب «تنظیمات» (Settings) تغییر دهید.'),
            ],
        },
        {
            'title': 'قبل از شروع',
            'blocks': [
                ('p', 'قبل از اسکن، VPN را کاملاً خاموش کنید. اسکن باید پینگ را مستقیم از سیستم شما به هر سرور اندازه بگیرد. اگر VPN هنوز روشن باشد، پینگ اندازه‌گیری‌شده سرعت واقعی شما را نشان نمی‌دهد.'),
                ('ol', [
                    'VPN را کاملاً خاموش کنید. مطمئن شوید اتصال قطع شده و برنامه‌ی VPN بسته است، نه فقط متوقف (pause) شده.',
                    'اتصال اینترنت خود را بررسی کنید؛ مثلاً یک وب‌سایت معمولی را در مرورگر باز کنید.',
                    'ProtonVPN Scanner را باز کنید و مراحل بخش بعد را دنبال کنید.',
                ]),
                ('note', 'اگر مطمئن نیستید VPN خاموش است، قبل از شروع اسکن، خود برنامه‌ی VPN را بررسی کنید.'),
            ],
        },
        {
            'title': 'مراحل اسکن',
            'blocks': [
                ('ol', [
                    '«بارگذاری دیتابیس» (Load database) را بزنید. برنامه فهرست سرورها را از آینه‌های GitHub (نسخه‌هایی از همان فایل روی سرورهای دیگر) دانلود می‌کند. این فهرست یک ساعت در کامپیوتر شما نگه داشته می‌شود. اگر نسخه‌ی ذخیره‌شده هنوز تازه باشد، همان استفاده می‌شود و دوباره دانلود نمی‌شود.',
                    'نوع سرور را انتخاب کنید: «رایگان» (Free) سرورهای رایگان، «پولی» (Premium) سرورهای پولی، و «همه» (All) هر دو را نشان می‌دهد.',
                    'اختیاری: در منوی کشویی «همه‌ی قاره‌ها» (All continents) یک قاره و در منوی کشویی «همه‌ی کشورها» (All countries) یک کشور انتخاب کنید. برای دیدن همه‌ی سرورها، هر دو را روی حالت همه بگذارید.',
                    '«شروع اسکن (۵۰۰)» (Start scan (500)) را بزنید. برنامه در یک مرحله پینگ ۵۰۰ سرور را می‌سنجد و سرورهایی را که پاسخ می‌دهند، یعنی سرورهای فعال، نگه می‌دارد.',
                    'برای سنجیدن ۵۰۰ سرور بعدی، «۵۰۰ بعدی» (Next 500) را بزنید. این کار را تا جایی که نتیجه‌ی کافی داشته باشید تکرار کنید.',
                    'برای شروع دوباره از اول، «شروع از نو» (Reset) را بزنید.',
                    'نتیجه‌ها در تب سرورها، سریع‌ترین‌ها اول، نشان داده می‌شوند. ۱۵ سرور برتر نمایش داده می‌شود.',
                ]),
                ('p', '«بارگذاری دوباره» (Reload database) همیشه یک نسخه‌ی تازه از فهرست را دانلود می‌کند. اگر شبکه کار نکند، به نسخه‌ی قدیمی ذخیره‌شده برمی‌گردد.'),
                ('p', 'هر سروری که پینگ آن کمتر از ۱۰ میلی‌ثانیه (ms) باشد، جعلی (fake) در نظر گرفته می‌شود و از نتایج کنار گذاشته می‌شود.'),
                ('note', 'برای بیشتر موارد، «بارگذاری دیتابیس» کافی است. «بارگذاری دوباره» را وقتی بزنید که بخواهید تازه‌ترین فهرست سرورها را داشته باشید.'),
            ],
        },
        {
            'title': 'تب سرورها و دکمه‌های هر کارت',
            'blocks': [
                ('p', 'تب سرورها نتیجه‌ی اسکن را نشان می‌دهد. هر سرور یک کارت جدا دارد. در بالای این تب، کادر «کلید خصوصی WireGuard» (WireGuard private key) قرار دارد و زیر آن دو دکمه هست: «خروجی ۱۵ سرور برتر (.conf)» (Export top 15 (.conf)) و «کپی لینک‌های wg://» (Copy wg:// links). این دو دکمه در بخش بعد توضیح داده شده‌اند.'),
                ('p', 'کلید خصوصی (private key) یک رمز مخفی است و مثل رمز عبور عمل می‌کند. در بخش کلید، این یادداشت نوشته شده: «فقط در همین پنجره نگه داشته می‌شود. فقط داخل فایل‌های .conf که ذخیره یا خروجی می‌گیرید نوشته می‌شود.»'),
                ('ul', [
                    'کپی IP (Copy IP): IP سرور را کپی می‌کند. IP یعنی آدرس عددی سرور.',
                    'کپی لینک (Copy link): یک لینک wg:// فقط برای همین سرور کپی می‌کند. این دکمه به کلید خصوصی نیاز دارد.',
                    'کپی WG (Copy WG): کل متن کانفیگ WireGuard این سرور را کپی می‌کند. بدون کلید هم کار می‌کند، اما متن شامل جای‌نگهدار <PASTE_YOUR_PRIVATE_KEY> است که باید دستی با کلید واقعی عوض شود.',
                    'QR: یک کد QR از کانفیگ این سرور نشان می‌دهد. این دکمه هم به کلید خصوصی نیاز دارد.',
                    'ذخیره .conf (Save .conf): کانفیگ این سرور را به‌صورت فایل ذخیره می‌کند. بدون کلید هم کار می‌کند، اما فایل شامل همان جای‌نگهدار است که باید دستی عوض شود.',
                ]),
                ('note', 'کد QR و لینک wg:// به کلید خصوصی نیاز دارند. اول کلید را در کادر وارد کنید.'),
            ],
        },
        {
            'title': 'کپی لینک‌های wg:// و خروجی گرفتن',
            'blocks': [
                ('p', 'لینک wg:// یک لینک متنی است که تنظیمات WireGuard یک سرور را توصیف می‌کند. این لینک هم به کلید خصوصی نیاز دارد.'),
                ('p', 'قالب لینک wg:// با برنامه‌ی Shadowrocket آزمایش شده است. برای برنامه‌های دیگر، از فایل‌های .conf یا کد QR استفاده کنید.'),
                ('ul', [
                    'کپی لینک (Copy link) در کارت هر سرور، فقط لینک همان سرور را کپی می‌کند.',
                    'کپی لینک‌های wg:// (Copy wg:// links) زیر کادر کلید، برای هر سرور اسکن‌شده‌ای که با قاره و کشور انتخابی شما مطابقت دارد، یک لینک کپی می‌کند. اگر هر دو را روی همه گذاشته باشید، همه‌ی سرورهای اسکن‌شده را شامل می‌شود.',
                    'خروجی ۱۵ سرور برتر (.conf) (Export top 15 (.conf)) فایل‌های کانفیگ ۱۵ سرور سریع‌تر را ذخیره می‌کند.',
                ]),
                ('warn', 'اگر کلید خصوصی را وارد کرده باشید، هر فایل .conf، هر لینک wg://، هر کد QR و هر متنی که با کپی WG (Copy WG) کپی شود، آن را دارد. همه‌ی این‌ها را محرمانه نگه دارید.'),
            ],
        },
        {
            'title': 'تست واقعی با یک کلاینت',
            'blocks': [
                ('p', 'برنامه سرورها را فقط با آزمون پینگ غربال می‌کند. سروری که «سالم» نشان داده می‌شود یعنی به پینگ اولیه جواب داده است. این یعنی احتمالاً در دسترس است، اما تضمین نمی‌کند که وصل شود، سرعت خوبی داشته باشد یا ترافیک شما را درست عبور دهد.'),
                ('p', 'برای تست واقعی، لینک‌های wg:// یا فایل‌های .conf را در یک کلاینت VPN بگذارید که بتواند چند کانفیگ را پشت سر هم تست کند. فقط سرورهایی را نگه دارید که واقعاً وصل می‌شوند و سرعت خوبی دارند.'),
                ('ul', [
                    'Shadowrocket: برای iPhone و iPad، از App Store. لینک‌های wg:// را می‌خواند و پولی است. فرمت این لینک‌ها با همین برنامه آزمایش شده است.',
                    'AmneziaVPN: برنامه‌ی اصلی کلاینت Amnezia و متن‌باز است. برای ویندوز، macOS، لینوکس، اندروید و iPhone منتشر شده است. فایل .conf را از SAVE .CONF یا EXPORT بگیرید و روش وارد کردن آن را در خود برنامه بررسی کنید.',
                ]),
                ('link', ('Shadowrocket در App Store', 'https://apps.apple.com/app/shadowrocket/id932747118')),
                ('link', ('AmneziaVPN: وب‌سایت', 'https://amnezia.org/')),
                ('link', ('AmneziaVPN: کد منبع در GitHub', 'https://github.com/amnezia-vpn/amnezia-client')),
                ('p', 'دو کلاینت بتا هم با دعوت TestFlight در دسترس‌اند. برای نصب آن‌ها باید برنامه‌ی TestFlight روی iPhone یا iPad باشد. ممکن است ظرفیت بتا پر باشد یا بعد از مدتی منقضی شود.'),
                ('link', ('CoreForge (TestFlight)', 'https://testflight.apple.com/join/YqwS1qtj')),
                ('link', ('ForgeCore (TestFlight)', 'https://testflight.apple.com/join/Z4rvxEwk')),
                ('note', 'اگر سروری در کلاینت وصل نشد، این موارد را بررسی کنید: کلید خصوصی درست کپی شده باشد، پارامترهای AmneziaWG با سرور یکی باشند و سرور AmneziaWG را پشتیبانی کند. سرور بعدی را هم امتحان کنید.'),
                ('warn', 'کلاینت‌ها هم کلید خصوصی شما را روی دستگاه خود نگه می‌دارند. فقط کانفیگ‌هایی را وارد کنید که خودتان ساخته‌اید، و کانفیگ‌هایی را که دیگر لازم نیستند از کلاینت حذف کنید.'),
            ],
        },
        {
            'title': 'گرفتن کلید خصوصی WireGuard از Proton',
            'blocks': [
                ('p', 'کلید خصوصی بخشی از کانفیگ WireGuard است که Proton برای حساب شما می‌سازد. برای کد QR، لینک wg:// و کانفیگ کامل بدون جای‌نگهدار به آن نیاز دارید.'),
                ('p', 'منوهای سایت Proton ممکن است تغییر کنند، پس نام‌های زیر ممکن است کمی متفاوت باشد. این مراحل را دنبال کنید:'),
                ('ol', [
                    'در مرورگر، account.protonvpn.com را باز کنید و با نام کاربری و رمز عبور Proton Account خود وارد شوید.',
                    'گزینه‌ی Downloads را باز کنید و بعد WireGuard configuration را انتخاب کنید.',
                    'یک پلتفرم انتخاب کنید. آنچه برای این برنامه مهم است این است که فایل .conf دانلودشده یک خط داشته باشد که با PrivateKey = شروع می‌شود. اگر این خط نبود، گزینه‌ی پلتفرم دیگری را امتحان کنید.',
                    'کانفیگ را بسازید و همان لحظه دانلود کنید. کلید خصوصی فقط مدت کوتاهی بعد از ساخت کانفیگ نشان داده می‌شود. دانلودهای بعدی کلید را به‌جای متن واقعی، فقط با نماد ستاره (*) نشان می‌دهند.',
                    'فایل را با یک ویرایشگر متن ساده باز کنید؛ مثلاً TextEdit در Mac یا Notepad در Windows.',
                    'فقط خود کلید را کپی کنید. این متنِ بعد از علامت = در خطِ PrivateKey است. کلید حدود ۴۴ کاراکتر دارد و با علامت = تمام می‌شود. عبارت PrivateKey = را کپی نکنید.',
                    'کلید را در کادر «کلید خصوصی WireGuard» (WireGuard private key) برنامه بچسبانید.',
                ]),
                ('p', 'اگر فایل به‌جای کلید نماد ستاره نشان می‌دهد، یک کانفیگ جدید بسازید، چند ثانیه صبر کنید و دوباره دانلود کنید.'),
            ],
        },
        {
            'title': 'امنیت کلید',
            'blocks': [
                ('warn', 'هرگز کلید خصوصی خود را در چت، در عکس صفحه، در انجمن‌ها یا در GitHub به اشتراک نگذارید. هرکسی که کلید را داشته باشد، می‌تواند از کانفیگ شما استفاده کند.'),
                ('p', 'وقتی کلید را وارد کرده باشید، این موارد همگی آن را در خود دارند: فایل‌های .conf، لینک‌های wg://، کدهای QR و متنی که با کپی WG (Copy WG) کپی شده است.'),
                ('p', 'برنامه کلید را در تنظیمات یا حافظه‌ی دائمی ذخیره نمی‌کند. کلید فقط در پنجره‌ی برنامه می‌ماند. تنها فایل‌های .conf که خودتان ذخیره یا خروجی می‌گیرید کلید را دارند.'),
                ('ul', [
                    'فایل‌های .conf، لینک‌های wg:// و عکس کدهای QR را برای هیچ‌کس نفرستید.',
                    'بعد از کپی کردن کلید یا کانفیگ، کلیپ‌بورد (جایی که متن کپی‌شده نگه داشته می‌شود) را با کپی کردن چیز بی‌ضرری، مثل یک کلمه‌ی ساده، پاک کنید.',
                    'فایل‌های .conf را که دیگر لازم ندارید حذف کنید.',
                ]),
                ('warn', 'اگر احتمال می‌دهید کلیدتان فاش شده باشد، در Proton یک کانفیگ جدید بسازید و از کانفیگ قبلی دیگر استفاده نکنید.'),
            ],
        },
        {
            'title': 'تنظیمات پنهان‌سازی AmneziaWG و بازگردانی',
            'blocks': [
                ('p', 'پنهان‌سازی (obfuscation) باعث می‌شود دست‌دهی WireGuard از چشم فیلترها پنهان بماند. دست‌دهی (handshake) اولین تبادل پیام‌ها برای برقراری اتصال است. روش پنهان‌سازی در این برنامه AmneziaWG نام دارد.'),
                ('p', 'گزینه‌ی «پنهان‌سازی AmneziaWG» (AmneziaWG obfuscation) در تب تنظیمات (Settings) قرار دارد و به‌طور پیش‌فرض روشن است.'),
                ('ul', [
                    'وقتی این گزینه روشن باشد، کانفیگ‌ها این پارامترها را دارند: Jc، Jmin، Jmax، S1، S2، H1، H2، H3 و H4. نام فایل‌ها هم پسوند _awg.conf می‌گیرد.',
                    'وقتی خاموش باشد، کانفیگ‌ها WireGuard ساده هستند.',
                ]),
                ('p', 'مقادیر پیشنهادی این‌ها هستند:'),
                ('ul', [
                    'Jc: 4',
                    'Jmin: 50',
                    'Jmax: 1000',
                    'S1: 0',
                    'S2: 0',
                    'H1: 1',
                    'H2: 2',
                    'H3: 3',
                    'H4: 4',
                ]),
                ('p', 'این مقادیر از یک نمونه‌ی کاری AmneziaWG گرفته شده‌اند و تضمین نمی‌شود که با همه‌ی سرورها کار کنند.'),
                ('warn', 'سروری که به آن وصل می‌شوید باید AmneziaWG را با همین عددها پشتیبانی کند. تنظیم این عددها در برنامه، به‌تنهایی کافی نیست.'),
                ('p', 'Jmin نباید از Jmax بزرگ‌تر باشد.'),
                ('p', 'برای برگرداندن عددهای پیشنهادی، در تب تنظیمات، دکمه‌ی «بازگردانی مقادیر پیشنهادی» (Reset to suggested values) را بزنید.'),
                ('note', 'اگر سرور از AmneziaWG استفاده نمی‌کند، این گزینه را خاموش کنید تا کانفیگ WireGuard ساده بگیرید.'),
            ],
        },
        {
            'title': 'مشکل‌های رایج',
            'blocks': [
                ('ul', [
                    'نتیجه‌ی پینگ عجیب یا نامنظم است: احتمالاً VPN هنگام اسکن روشن بوده است. آن را کاملاً خاموش کنید و دوباره اسکن کنید.',
                    'دیتابیس بارگذاری نمی‌شود: اتصال اینترنت را بررسی کنید و وقتی شبکه برقرار شد، «بارگذاری دوباره» (Reload database) را بزنید. اگر شبکه کار نکند و نسخه‌ی ذخیره‌شده‌ای وجود داشته باشد، برنامه از همان استفاده می‌کند. اگر هنوز هیچ نسخه‌ای ذخیره نشده، برای دانلود اولیه به اینترنت نیاز دارید.',
                    'سروری را که انتظار دارید در نتایج نیست: سرورهایی که پینگ آن‌ها کمتر از ۱۰ میلی‌ثانیه (ms) است، جعلی در نظر گرفته و کنار گذاشته می‌شوند. همچنین فیلترهای نوع سرور، قاره و کشور را بررسی کنید.',
                    'برنامه کلید را می‌خواهد: قبل از استفاده از «کپی لینک» (Copy link) یا QR، کلید خصوصی WireGuard را وارد کنید. این دو به کلید نیاز دارند.',
                    'برنامه می‌گوید کلید معتبر نیست: بررسی کنید که فقط خود کلید را کپی کرده باشید؛ حدود ۴۴ کاراکتر که با علامت = تمام می‌شود، بدون عبارت PrivateKey =.',
                    'فایل Proton به‌جای کلید ستاره نشان می‌دهد: یک کانفیگ جدید بسازید، چند ثانیه صبر کنید و دوباره دانلود کنید.',
                    'کانفیگ شامل <PASTE_YOUR_PRIVATE_KEY> است: یعنی بدون کلید کپی یا ذخیره شده است. این عبارت را دستی با کلید واقعی خود عوض کنید، یا کلید را وارد کنید و دوباره کپی یا ذخیره کنید.',
                    'لینک wg:// در برنامه‌ی شما کار نمی‌کند: قالب لینک فقط با Shadowrocket آزمایش شده است. برای برنامه‌های دیگر از فایل .conf یا کد QR استفاده کنید.',
                    'کانفیگ AmneziaWG کار نمی‌کند: سرور باید AmneziaWG را با همان عددها پشتیبانی کند. اگر سرور از AmneziaWG استفاده نمی‌کند، گزینه‌ی پنهان‌سازی را خاموش کنید تا کانفیگ WireGuard ساده بگیرید.',
                    'Jmin بزرگ‌تر از Jmax است: Jmin نباید از Jmax بزرگ‌تر باشد. مقادیر را در تب تنظیمات اصلاح کنید.',
                ]),
            ],
        },
        {
            'title': 'محل ذخیره فایل‌ها',
            'blocks': [
                ('p', 'فایل‌ها وقتی ذخیره می‌شوند که روی «ذخیره .conf» (Save .conf) در کارت یک سرور یا «خروجی ۱۵ سرور برتر (.conf)» (Export top 15 (.conf)) بزنید.'),
                ('p', 'بعد از ذخیره‌ی فایل، یک پیام کوتاه پایین صفحه چند ثانیه مسیر فایل را نشان می‌دهد. همان مسیر را یادداشت کنید تا فایل را پیدا کنید.'),
                ('p', 'کانفیگ‌هایی که پنهان‌سازی آن‌ها روشن است، در نام فایل پسوند _awg.conf دارند. کانفیگ‌هایی که پنهان‌سازی آن‌ها خاموش است، این پسوند را ندارند.'),
                ('note', 'کپی WG (Copy WG) متن کانفیگ را در کلیپ‌بورد کپی می‌کند و فایلی نمی‌سازد.'),
                ('warn', 'اگر کلید خصوصی خود را وارد کرده باشید، فایل ذخیره‌شده‌ی .conf محرمانه است. آن را در جای امنی نگه دارید و وقتی دیگر لازم نیست، حذفش کنید.'),
            ],
        },
    ],
    'en': [
        {
            'title': 'What the app does',
            'blocks': [
                ('p', 'ProtonVPN Scanner gets the list of ProtonVPN servers, measures how fast each server answers, and shows the fastest ones first.'),
                ('p', 'Speed is measured as ping. Ping is the time a small message needs to go to a server and come back. It is measured in milliseconds (ms). A lower number is faster.'),
                ('p', 'For the servers it finds, the app can also build WireGuard config files. A config is a settings file. A WireGuard app reads it to connect to a server.'),
                ('p', 'A server shown as alive has only passed the first ping test. To be sure it works, test it in a real client. See the section "Test for real with a client app".'),
                ('ul', [
                    'Load the server list. In this app the list is called the database.',
                    'Choose the server type (Free, Premium or All). If you need, also choose a continent and a country.',
                    'Start a scan to find the servers that are alive, meaning the servers that answer.',
                    'Copy a server IP. An IP is the numeric address of a server. You can also copy a server config, or save it as a file.',
                ]),
                ('p', 'This guide is in the Guide tab. You can change the language (English or فارسی) in the Settings tab.'),
            ],
        },
        {
            'title': 'Before you start',
            'blocks': [
                ('p', 'Turn the VPN fully off before you scan. The scan must measure ping directly from your computer to each server. If the VPN is still on, the measured ping does not show your real speed.'),
                ('ol', [
                    'Turn the VPN off completely. Make sure it is disconnected and its app is closed, not only paused.',
                    'Check that your internet connection works, for example by opening a normal website in your browser.',
                    'Open ProtonVPN Scanner and follow the steps in the next section.',
                ]),
                ('note', 'If you are not sure the VPN is off, check the VPN app before you start the scan.'),
            ],
        },
        {
            'title': 'Step by step scan',
            'blocks': [
                ('ol', [
                    'Press Load database. The app downloads the server list from GitHub mirrors (copies of the same file on other servers). The list is kept on your computer for one hour. If the saved copy is still fresh, Load database uses it and does not download again.',
                    'Choose a server type. Free shows free servers, Premium shows paid servers, and All shows both.',
                    'Optional: in the All continents dropdown choose one continent, and in the All countries dropdown choose one country. Leave both on All to include every server.',
                    'Press Start scan (500). The app measures the ping of 500 servers in one round. It keeps the servers that answer. These are called alive servers.',
                    'To test the next 500 servers, press Next 500. Repeat as needed until you have enough results.',
                    'To start again from the beginning, press Reset.',
                    'Results appear on the Servers tab, fastest first. The top 15 are shown.',
                ]),
                ('p', 'Reload database always downloads a fresh copy of the list. If the network fails, it falls back to the old saved copy.'),
                ('p', 'Any server whose ping is under 10 milliseconds is treated as fake and dropped from the results.'),
                ('note', 'Load database is enough for most scans. Use Reload database when you want the newest server list.'),
            ],
        },
        {
            'title': 'The Servers tab and the buttons on each server card',
            'blocks': [
                ('p', 'The Servers tab shows the results of your scan. Each server has its own card. At the top of the tab is the WireGuard private key field. Below it are two buttons: Export top 15 (.conf) and Copy wg:// links. These two buttons are explained in the next section.'),
                ('p', 'The WireGuard private key is a secret, like a password. The field has this note: Kept only in this window. Never saved or shared by the app.'),
                ('ul', [
                    'Copy IP: copies the IP of the server. An IP is the numeric address of the server.',
                    'Copy link: copies one wg:// link for this server. This button needs the private key.',
                    'Copy WG: copies the full WireGuard config text for this server. It works without the key, but then the text contains the placeholder <PASTE_YOUR_PRIVATE_KEY>, which you must replace by hand.',
                    'QR: shows a QR code of the config for this server. This button needs the private key.',
                    'Save .conf: saves the config for this server as a file. It works without the key, but then the file contains the placeholder, which you must replace by hand.',
                ]),
                ('note', 'QR codes and wg:// links need the private key. Enter the key in the field before you use these buttons.'),
            ],
        },
        {
            'title': 'Copying wg:// links and exporting configs',
            'blocks': [
                ('p', 'A wg:// link is a text link that describes the WireGuard settings of one server. It needs your private key.'),
                ('p', 'The wg:// link format was tested with the Shadowrocket app. For other apps, use the .conf files or the QR code instead.'),
                ('ul', [
                    'Copy link (on a server card) copies the wg:// link of that one server.',
                    'Copy wg:// links (below the key field) copies one link for each scanned server that matches the continent and country you chose. If you left both on All, it covers all scanned servers.',
                    'Export top 15 (.conf) saves config files for the 15 fastest servers in the results.',
                ]),
                ('warn', 'If you have entered your private key, every .conf file, wg:// link, QR code and text copied with Copy WG contains it. Treat all of them as secret.'),
            ],
        },
        {
            'title': 'Test for real with a client app',
            'blocks': [
                ('p', 'The app screens servers with a ping test only. A server shown as alive has answered the first ping. This means it is probably reachable, but it does not guarantee that it connects, is fast, or carries your traffic correctly.'),
                ('p', 'For a real test, put the wg:// links or .conf files into a VPN client that can test several configs in a row. Keep only the servers that really connect and are fast.'),
                ('ul', [
                    'Shadowrocket: for iPhone and iPad, from the App Store. It reads wg:// links and it is a paid app. The wg:// format used here was tested with this app.',
                    'AmneziaVPN: the main Amnezia client. It is open source and available for Windows, macOS, Linux, Android and iPhone. Take the .conf file from SAVE .CONF or EXPORT, and check the import steps inside the app.',
                ]),
                ('link', ('Shadowrocket on the App Store', 'https://apps.apple.com/app/shadowrocket/id932747118')),
                ('link', ('AmneziaVPN website', 'https://amnezia.org/')),
                ('link', ('AmneziaVPN source code on GitHub', 'https://github.com/amnezia-vpn/amnezia-client')),
                ('p', 'Two beta clients are also available by TestFlight invitation. To install them, you need the TestFlight app on your iPhone or iPad. A beta may be full or may expire after a while.'),
                ('link', ('CoreForge (TestFlight)', 'https://testflight.apple.com/join/YqwS1qtj')),
                ('link', ('ForgeCore (TestFlight)', 'https://testflight.apple.com/join/Z4rvxEwk')),
                ('note', 'If a server does not connect in the client, check these: the private key was copied correctly, the AmneziaWG parameters match the server, and the server supports AmneziaWG. Then try the next server.'),
                ('warn', 'Clients also keep your private key on the device. Only import configs that you made yourself, and delete the configs you no longer need from the client.'),
            ],
        },
        {
            'title': 'Getting your WireGuard private key from Proton',
            'blocks': [
                ('p', 'The private key is part of the WireGuard configuration that Proton creates for your account. You need it for QR codes, for wg:// links, and for a complete config without the placeholder.'),
                ('p', 'Proton may change its menus, so the names below may look a little different. Follow these steps:'),
                ('ol', [
                    'In a browser, open account.protonvpn.com and sign in with your Proton Account username and password.',
                    'Open Downloads, then choose WireGuard configuration.',
                    'Choose a platform. What matters for this app is that the downloaded .conf file has a line that starts with PrivateKey =. If the file does not have that line, try another platform option.',
                    'Create the config and download it right away. The private key is shown only briefly after the config is created. A later download shows the key as asterisk symbols (*) instead of the real text.',
                    'Open the file in a plain text editor, such as TextEdit on Mac or Notepad on Windows.',
                    'Copy only the key. It is the text after the = sign on the PrivateKey line. The key is about 44 characters long and ends with an = sign. Do not copy the words PrivateKey =.',
                    'Paste the key into the WireGuard private key field in the app.',
                ]),
                ('p', 'If the file shows asterisk symbols (*) instead of the key, create a new config, wait a few seconds, and download it again.'),
            ],
        },
        {
            'title': 'Keeping your key safe',
            'blocks': [
                ('warn', 'Never share your private key in a chat, in a screenshot, on a forum, or on GitHub. Anyone who has the key can use your config.'),
                ('p', 'Once you have entered your key, these all contain it: .conf files, wg:// links, QR codes, and text copied with Copy WG.'),
                ('p', 'The app does not save the key in its settings, and it stays only in the app window. Only the .conf files you save or export contain it.'),
                ('ul', [
                    'Do not send .conf files, wg:// links or QR code pictures to anyone.',
                    'After you copy the key or a config, clear the clipboard (the place where copied text is kept) by copying something harmless, such as a single word.',
                    'Delete .conf files that you no longer need.',
                ]),
                ('warn', 'If you think your key may have leaked, create a new config in Proton and stop using the old one.'),
            ],
        },
        {
            'title': 'AmneziaWG obfuscation settings and reset',
            'blocks': [
                ('p', 'Obfuscation hides the WireGuard handshake from filters. The handshake is the first exchange of messages that sets up a connection. In this app the hiding method is called AmneziaWG.'),
                ('p', 'The AmneziaWG obfuscation switch is on the Settings tab. It is on by default.'),
                ('ul', [
                    'When the switch is on, configs include these parameters: Jc, Jmin, Jmax, S1, S2, H1, H2, H3 and H4. File names get the suffix _awg.conf.',
                    'When the switch is off, the configs are plain WireGuard configs.',
                ]),
                ('p', 'The suggested values are:'),
                ('ul', [
                    'Jc: 4',
                    'Jmin: 50',
                    'Jmax: 1000',
                    'S1: 0',
                    'S2: 0',
                    'H1: 1',
                    'H2: 2',
                    'H3: 3',
                    'H4: 4',
                ]),
                ('p', 'These values come from one working AmneziaWG sample. They are not guaranteed to work with every server.'),
                ('warn', 'The server you connect to must support AmneziaWG with the same numbers. Changing the numbers in this app alone is not enough.'),
                ('p', 'Jmin must not be larger than Jmax.'),
                ('p', 'To restore the suggested numbers, press Reset to suggested values on the Settings tab.'),
                ('note', 'If the server does not use AmneziaWG, turn the switch off to get plain WireGuard configs.'),
            ],
        },
        {
            'title': 'Common problems',
            'blocks': [
                ('ul', [
                    'The ping numbers look wrong or unstable: the VPN was probably on during the scan. Turn it fully off and scan again.',
                    'The database does not load: check your internet connection. When the network works again, press Reload database. If the network fails and a saved copy exists, the app uses that copy. If no copy has ever been saved, you need an internet connection to download the list.',
                    'A server you expected is missing from the results: servers with a ping under 10 milliseconds (ms) are treated as fake and dropped. Also check the server type, continent and country filters.',
                    'The app asks for a key: enter your WireGuard private key before you use Copy link or QR. These two need it.',
                    'The app says the key is not valid: check that you copied only the key, about 44 characters that end with an = sign, and not the words PrivateKey =.',
                    'The Proton file shows asterisk symbols (*) instead of the key: create a new config, wait a few seconds, and download it again.',
                    'The config contains <PASTE_YOUR_PRIVATE_KEY>: this text was copied or saved without a key. Replace it by hand with your real key, or enter the key first and then copy or save again.',
                    'A wg:// link does not work in your app: the link format was tested only with Shadowrocket. For other apps, use a .conf file or the QR code.',
                    'An AmneziaWG config does not work: the server must support AmneziaWG with the same numbers. If the server does not use AmneziaWG, turn the obfuscation switch off to get plain WireGuard configs.',
                    'Jmin is larger than Jmax: Jmin must not be larger than Jmax. Fix the values on the Settings tab.',
                ]),
            ],
        },
        {
            'title': 'Where files are saved',
            'blocks': [
                ('p', 'Files are saved when you press Save .conf on a server card, or Export top 15 (.conf).'),
                ('p', 'After a file is saved, a short message at the bottom of the screen shows its path for a few seconds. Write the path down so you can find the file.'),
                ('p', 'Configs made with obfuscation on have the suffix _awg.conf in their file names. Configs made with obfuscation off do not have this suffix.'),
                ('note', 'Copy WG copies the config text to the clipboard. It does not create a file.'),
                ('warn', 'If you have entered your private key, a saved .conf file is secret. Keep it in a safe place, and delete it when you no longer need it.'),
            ],
        },
    ],
}
