const API_BASE = window.BUILDYOURPC_API || '';

const state = {
  step: 1,
  device_type: 'desktop',
  budget: 800,
  currency: 'USD',
  country: 'US',
  language: 'en',
  use_cases: ['Gaming'],
  games: [],
  preferences: [],
  existing_parts: [],
  target_fps: null,
  resolution: null,
  result: null,
  preset: 'smart'
};

const el = (id) => document.getElementById(id);
const q = (sel, root=document) => root.querySelector(sel);
const qa = (sel, root=document) => [...root.querySelectorAll(sel)];
let config = {countries:[], languages:[], games:[], currencies:{}, kofi:'https://ko-fi.com/simbawwyy00'};
let busyActions = new Set();

const TRANSLATIONS = {
  en: {
    continue:'Continue', matching:'Matching', skip:'Skip', back:'Back', edit:'Edit', support:'Support', explore:'Explore', how:'How it works', results:'Results',
    startBuilding:'Start building', exploreBuilds:'Explore builds', leaveTip:'Leave a Tip', buildsCreated:'builds created', buildViews:'build views', shares:'shares',
    smarterWay:'A smarter way to buy your next computer', heroTitle:'Build the PC<br><em>you actually need.</em>', heroSub:'Tell us your budget, your world, and what matters. BuildYourPC finds the smartest machine for your money — not the most expensive one.',
    livePreview:'LIVE PREVIEW', matchingLive:'matching', yourBudget:'Your budget', bestFit:'Best-fit', findSweet:'FIND THE SWEET SPOT', compareReal:'COMPARE THE REAL OPTIONS', spendSmarter:'SPEND SMARTER', buildConfidence:'BUILD WITH CONFIDENCE',
    discover:'01 · DISCOVER', makeEasy:"Let’s make this easy.", discoverSub:'Only budget is required. Everything else simply makes the match sharper.',
    stepOf:'Step {n} of 5', whatLooking:'WHAT ARE WE LOOKING FOR?', machineTitle:'Pick the kind of machine.<br><em>Or let us decide.</em>', machineSub:'You can change this later without starting over.', desktop:'Desktop PC', desktopSub:'Build or buy a desktop', laptop:'Laptop', laptopSub:'Portable gaming & work', prebuilt:'Prebuilt', prebuiltSub:'Ready to use', custom:'Custom build', customSub:'More control, same goal', used:'Used / refurbished', usedSub:'Stretch the budget', notSure:'I’m not sure', notSureSub:'Help me decide',
    budgetQuestion:'HOW MUCH ARE WE WORKING WITH?', budgetTitle:'Your budget is the <em>hard ceiling.</em>', budgetSub:'We won’t spend money just because it’s available.', budgetLabel:'Budget', budgetHint:'You can always refine the result later.',
    usingFor:'WHAT ARE YOU USING IT FOR?', goalsTitle:'Choose what <em>matters most.</em>', optional:'Nothing here is mandatory.', gaming:'Gaming', gamingSub:'I want games to feel great', streaming:'Gaming + streaming', streamingSub:'Play and broadcast', creation:'Creation', creationSub:'Edit, render, create', work:'Work + play', workSub:'One machine for everything', ai:'AI / compute', aiSub:'Local workloads matter', futureProof:'Future-proof', futureSub:'Keep it useful longer',
    giveMore:'GIVE US A LITTLE MORE', tighterMatch:'Only if you want a <em>tighter match.</em>', skipUnknown:'Skip anything you don’t know.', games:'Games', matters:'What matters?', targetFps:'Target FPS', resolution:'Resolution', quiet:'🤫 Quiet', wifi:'📶 Wi-Fi', small:'📦 Small', future:'🚀 Future-proof', notSureShort:'Not sure',
    lastCheck:'LAST QUICK CHECK', ownAnything:'Do you already own <em>anything?</em>', avoidDuplicates:'We’ll avoid buying duplicates.', monitor:'Monitor', ssd:'SSD', ram:'RAM', case:'Case', psu:'Power supply', nothingYet:'Nothing yet', budgetEnough:'Budget is enough to start.', everythingOptional:'Everything else is optional.', readyWhen:'Ready when you are.',
    match:'02 · MATCH', translated:'Your money, <em>translated.</em>', matchSub:'Results are ranked for fit — not just raw performance.', yourBrief:'YOUR BRIEF', market:'Market', direction:'Direction', smartBuy:'Smart Buy', speedDemon:'Speed Demon', beast:'The Beast', matchReady:'Match ready', value:'Value', futureScore:'Future', fpsEst:'FPS est.', fit:'FIT', live:'LIVE', reference:'REF', marketplace:'MARKET', viewStore:'View store',
    exploreSection:'03 · EXPLORE', exploreTitle:'Builds worth <em>stealing ideas from.</em>', exploreSub:'Shared builds are meant to be useful, remixable and honest about the trade-offs.', loading:'loading', loadingBuilds:'Loading live builds', buildsAppear:'Shared builds will appear here as people save them.',
    whyWorks:'04 · WHY IT WORKS', whyTitle:'No PC knowledge <em>required.</em>', whySub:'The point is to remove the guesswork, not add another spec sheet.', outcome:'You tell us the outcome.', outcomeSub:'Budget, device type, games, portability, noise — whatever you know. Nothing more is required.', protect:'We protect the budget.', protectSub:'A 144 FPS target is a floor, not an excuse to buy 300 FPS. We stop spending when the goal is already met.', tradeoffs:'We show the trade-offs.', tradeoffsSub:'Best value, fastest, quietest or most upgradeable — you can switch direction without rebuilding the whole brief.',
    keepFree:'KEEP IT FREE', freeTitle:'Built to help you spend smarter.', freeSub:'We want BuildYourPC to stay useful before it ever needs to be profitable.', freeMvp:'Free MVP · Global-ready · Built for mobile + desktop', backTop:'Back to top ↑',
    language:'LANGUAGE', languageTitle:'Speak your way.', searchLanguage:'Search language…', marketDock:'MARKET', marketTitle:'Where are we shopping?', searchCountry:'Search country…',
    continueHint:'Continue', addBudget:'Add a budget first.', buildFailed:'Build failed. Please try again.', saved:'Build saved — link copied.', saveFailed:'Could not save the build.', shareFailed:'Could not create a share link.', linkCopied:'Link copied.', languageSet:'Language set to', languageFallback:'Interface fallback: English is used for this language for now.', marketChanged:'Market changed to', offline:'Could not reach the API. Please check your connection and try again.', genericError:'Unable to complete this action. Please try again.', budgetRange:'Budget must be within the allowed range.',
    matchReadyText:'Match ready', smart:'Smart Buy', speed:'Speed Demon', beastLabel:'The Beast', estimatedTotal:'Estimated total', whyFits:'Why this fits', goalCheck:'Goal check', moneyMove:'Money move', save:'Save', share:'Share', copy:'Copy link', referenceNote:'Reference catalog — verify prices before buying.', liveNote:'Fresh live offers are active where available; reference prices remain clearly labeled.',
    savedLoaded:'Saved build loaded.', smartTitle:'The Smart Buy', speedTitle:'The Speed Demon', beastTitle:'The Beast', fit:'FIT', viewStore:'View store', shareTitle:'My BuildYourPC build', shareText:'I found this build on BuildYourPC.', chooseBest:'We’ll infer the best direction from your next answers.',
  },
  fr: {
    continue:'Continuer', matching:'Recherche', skip:'Passer', back:'Retour', edit:'Modifier', support:'Soutenir', explore:'Explorer', how:'Comment ça marche', results:'Résultats', startBuilding:'Commencer', exploreBuilds:'Explorer les configs', leaveTip:'Laisser un pourboire', buildsCreated:'configs créées', buildViews:'vues', shares:'partages',
    smarterWay:'Une façon plus intelligente d’acheter votre prochain ordinateur', heroTitle:'Construisez le PC<br><em>dont vous avez vraiment besoin.</em>', heroSub:'Indiquez votre budget, vos usages et vos priorités. BuildYourPC trouve la meilleure machine pour votre argent — pas la plus chère.',
    livePreview:'APERÇU EN DIRECT', matchingLive:'recherche', yourBudget:'Votre budget', bestFit:'Meilleur choix', findSweet:'TROUVEZ LE BON ÉQUILIBRE', compareReal:'COMPAREZ LES VRAIES OPTIONS', spendSmarter:'DÉPENSEZ MIEUX', buildConfidence:'CONSTRUISEZ EN CONFIANCE',
    discover:'01 · DÉCOUVRIR', makeEasy:'Simplifions les choses.', discoverSub:'Le budget suffit. Tout le reste affine simplement la recommandation.', stepOf:'Étape {n} sur 5', whatLooking:'QUE RECHERCHONS-NOUS ?', machineTitle:'Choisissez le type de machine.<br><em>Ou laissez-nous décider.</em>', machineSub:'Vous pourrez changer plus tard sans recommencer.', desktop:'PC fixe', desktopSub:'Construire ou acheter un PC', laptop:'Portable', laptopSub:'Jeux et travail mobiles', prebuilt:'Préassemblé', prebuiltSub:'Prêt à l’emploi', custom:'Configuration personnalisée', customSub:'Plus de contrôle, même objectif', used:'Occasion / reconditionné', usedSub:'Étirez le budget', notSure:'Je ne sais pas', notSureSub:'Aidez-moi à décider',
    budgetQuestion:'QUEL EST VOTRE BUDGET ?', budgetTitle:'Votre budget est le <em>plafond absolu.</em>', budgetSub:'Nous ne dépensons pas juste parce que l’argent est disponible.', budgetLabel:'Budget', budgetHint:'Vous pourrez toujours affiner le résultat.', usingFor:'À QUOI VA SERVIR LA MACHINE ?', goalsTitle:'Choisissez ce qui <em>compte le plus.</em>', optional:'Rien ici n’est obligatoire.', gaming:'Jeux', gamingSub:'Je veux une excellente expérience', streaming:'Jeux + streaming', streamingSub:'Jouer et diffuser', creation:'Création', creationSub:'Monter, rendre, créer', work:'Travail + jeux', workSub:'Une machine pour tout', ai:'IA / calcul', aiSub:'Charges locales importantes', futureProof:'Durable', futureSub:'La garder utile plus longtemps',
    giveMore:'DONNEZ-NOUS UN PEU PLUS', tighterMatch:'Seulement pour un <em>match plus précis.</em>', skipUnknown:'Ignorez ce que vous ne connaissez pas.', games:'Jeux', matters:'Priorités', targetFps:'FPS cible', resolution:'Résolution', quiet:'🤫 Silencieux', wifi:'📶 Wi-Fi', small:'📦 Compact', future:'🚀 Durable', notSureShort:'Je ne sais pas', lastCheck:'DERNIÈRE VÉRIFICATION', ownAnything:'Avez-vous déjà <em>quelque chose ?</em>', avoidDuplicates:'Nous éviterons les doublons.', monitor:'Écran', ssd:'SSD', ram:'RAM', case:'Boîtier', psu:'Alimentation', nothingYet:'Rien pour le moment', budgetEnough:'Le budget suffit pour commencer.', everythingOptional:'Tout le reste est facultatif.', readyWhen:'Prêt quand vous l’êtes.',
    match:'02 · MATCH', translated:'Votre argent, <em>traduit.</em>', matchSub:'Les résultats sont classés selon l’adéquation — pas seulement la puissance brute.', yourBrief:'VOTRE BESOIN', market:'Marché', direction:'Orientation', smartBuy:'Achat malin', speedDemon:'Performance', beast:'Le Monstre', matchReady:'Résultat prêt', value:'Valeur', futureScore:'Durée', fpsEst:'FPS estimés', fit:'COMPAT.', live:'DIRECT', reference:'RÉF.', marketplace:'MARCHÉ', viewStore:'Voir le magasin',
    exploreSection:'03 · EXPLORER', exploreTitle:'Des configurations dont <em>s’inspirer.</em>', exploreSub:'Les configurations partagées doivent être utiles, remixables et honnêtes sur les compromis.', loading:'chargement', loadingBuilds:'Chargement des configurations', buildsAppear:'Les configurations partagées apparaîtront ici.', whyWorks:'04 · POURQUOI ÇA MARCHE', whyTitle:'Aucune connaissance PC <em>requise.</em>', whySub:'Le but est d’enlever les devinettes, pas d’ajouter une fiche technique.', outcome:'Vous donnez le résultat souhaité.', outcomeSub:'Budget, type de machine, jeux, mobilité, bruit — tout ce que vous savez suffit.', protect:'Nous protégeons le budget.', protectSub:'Un objectif de 144 FPS est un minimum, pas une excuse pour acheter 300 FPS.', tradeoffs:'Nous montrons les compromis.', tradeoffsSub:'Meilleur rapport qualité/prix, rapidité, silence ou évolutivité — changez de direction sans tout refaire.', keepFree:'GARDEZ-LE GRATUIT', freeTitle:'Conçu pour vous aider à dépenser mieux.', freeSub:'BuildYourPC doit rester utile avant même de devenir rentable.', freeMvp:'MVP gratuit · Prêt pour le monde · Mobile + desktop', backTop:'Retour en haut ↑',
    language:'LANGUE', languageTitle:'Parlez comme vous voulez.', searchLanguage:'Rechercher une langue…', marketDock:'MARCHÉ', marketTitle:'Où achetons-nous ?', searchCountry:'Rechercher un pays…',
    continueHint:'Continuer', addBudget:'Ajoutez d’abord un budget.', buildFailed:'Échec de la configuration. Réessayez.', saved:'Configuration enregistrée — lien copié.', saveFailed:'Impossible d’enregistrer la configuration.', shareFailed:'Impossible de créer le lien de partage.', linkCopied:'Lien copié.', languageSet:'Langue définie sur', languageFallback:'Interface en anglais pour cette langue pour le moment.', marketChanged:'Marché défini sur', offline:'Impossible de joindre l’API. Vérifiez votre connexion puis réessayez.', genericError:'Impossible de terminer cette action. Réessayez.', budgetRange:'Le budget doit respecter la plage autorisée.', matchReadyText:'Résultat prêt', smart:'Achat malin', speed:'Performance', beastLabel:'Le Monstre', estimatedTotal:'Total estimé', whyFits:'Pourquoi ce choix', goalCheck:'Vérification', moneyMove:'Budget', save:'Enregistrer', share:'Partager', copy:'Copier le lien', referenceNote:'Catalogue de référence — vérifiez les prix avant achat.', liveNote:'Les offres en direct sont utilisées lorsqu’elles sont disponibles; les prix de référence restent identifiés.', savedLoaded:'Configuration enregistrée chargée.', smartTitle:'L’achat malin', speedTitle:'La performance', beastTitle:'Le monstre', fit:'COMPAT.', viewStore:'Voir le magasin', shareTitle:'Ma configuration BuildYourPC', shareText:'J’ai trouvé cette configuration sur BuildYourPC.', chooseBest:'Nous déterminerons la meilleure direction avec vos prochaines réponses.'
  },
  ar: {
    continue:'متابعة', matching:'جاري المطابقة', skip:'تخطي', back:'رجوع', edit:'تعديل', support:'دعم', explore:'استكشاف', how:'كيف يعمل', results:'النتائج', startBuilding:'ابدأ البناء', exploreBuilds:'استكشف التجميعات', leaveTip:'اترك دعمًا', buildsCreated:'تجميعات', buildViews:'مشاهدة', shares:'مشاركة',
    smarterWay:'طريقة أذكى لشراء جهازك القادم', heroTitle:'ابنِ الجهاز الذي<br><em>تحتاجه فعلًا.</em>', heroSub:'أخبرنا بميزانيتك واستخدامك وما يهمك. سيجد BuildYourPC الجهاز الأنسب لمالك — وليس الأغلى.',
    livePreview:'معاينة مباشرة', matchingLive:'مطابقة', yourBudget:'ميزانيتك', bestFit:'الأفضل لك', findSweet:'اعثر على الاختيار المناسب', compareReal:'قارن الخيارات الحقيقية', spendSmarter:'أنفق بذكاء', buildConfidence:'ابنِ بثقة',
    discover:'01 · اكتشاف', makeEasy:'لنجعل الأمر سهلًا.', discoverSub:'الميزانية وحدها تكفي. وكل شيء آخر يجعل المطابقة أدق.', stepOf:'الخطوة {n} من 5', whatLooking:'ماذا نبحث عنه؟', machineTitle:'اختر نوع الجهاز.<br><em>أو دعنا نقرر.</em>', machineSub:'يمكنك تغييره لاحقًا دون البدء من جديد.', desktop:'كمبيوتر مكتبي', desktopSub:'ابنِ أو اشترِ جهازًا مكتبيًا', laptop:'لابتوب', laptopSub:'ألعاب وعمل متنقل', prebuilt:'جاهز مسبقًا', prebuiltSub:'جاهز للاستخدام', custom:'تجميعة مخصصة', customSub:'تحكم أكبر، نفس الهدف', used:'مستعمل / مجدد', usedSub:'مدّد الميزانية', notSure:'لست متأكدًا', notSureSub:'ساعدني على الاختيار',
    budgetQuestion:'كم تبلغ الميزانية؟', budgetTitle:'ميزانيتك هي <em>الحد الأقصى.</em>', budgetSub:'لن ننفق أكثر لمجرد أن المال متاح.', budgetLabel:'الميزانية', budgetHint:'يمكنك دائمًا تحسين النتيجة لاحقًا.', usingFor:'في ماذا ستستخدمه؟', goalsTitle:'اختر ما <em>يهم أكثر.</em>', optional:'لا شيء هنا إلزامي.', gaming:'ألعاب', gamingSub:'أريد تجربة ألعاب ممتازة', streaming:'ألعاب + بث', streamingSub:'العب وابث', creation:'إنشاء المحتوى', creationSub:'مونتاج ورندر وإنشاء', work:'عمل + ألعاب', workSub:'جهاز واحد لكل شيء', ai:'ذكاء اصطناعي / حوسبة', aiSub:'الأحمال المحلية مهمة', futureProof:'مستقبلي', futureSub:'يبقى مفيدًا لمدة أطول',
    giveMore:'أعطنا المزيد قليلًا', tighterMatch:'فقط إذا أردت <em>مطابقة أدق.</em>', skipUnknown:'تجاوز ما لا تعرفه.', games:'الألعاب', matters:'ما الذي يهم؟', targetFps:'FPS المستهدف', resolution:'الدقة', quiet:'🤫 هادئ', wifi:'📶 Wi‑Fi', small:'📦 صغير', future:'🚀 مستقبلي', notSureShort:'غير متأكد', lastCheck:'آخر فحص سريع', ownAnything:'هل تملك بالفعل <em>أي شيء؟</em>', avoidDuplicates:'سنتجنب شراء القطع المكررة.', monitor:'شاشة', ssd:'SSD', ram:'RAM', case:'صندوق', psu:'مزود طاقة', nothingYet:'لا شيء بعد', budgetEnough:'الميزانية كافية للبدء.', everythingOptional:'كل شيء آخر اختياري.', readyWhen:'جاهز عندما تكون مستعدًا.',
    match:'02 · المطابقة', translated:'مالك، <em>بشكل مفهوم.</em>', matchSub:'يتم ترتيب النتائج حسب ملاءمتها لك، وليس الأداء الخام فقط.', yourBrief:'متطلباتك', market:'السوق', direction:'التوجه', smartBuy:'الشراء الذكي', speedDemon:'الأداء', beast:'الأقوى', matchReady:'النتيجة جاهزة', value:'القيمة', futureScore:'المستقبل', fpsEst:'FPS متوقع', fit:'ملاءمة', live:'مباشر', reference:'مرجعي', marketplace:'متجر', viewStore:'فتح المتجر',
    exploreSection:'03 · استكشاف', exploreTitle:'تجميعات تستحق <em>أخذ الأفكار منها.</em>', exploreSub:'التجميعات المشتركة مفيدة وقابلة للتعديل وصريحة بشأن التنازلات.', loading:'جارٍ التحميل', loadingBuilds:'جارٍ تحميل التجميعات', buildsAppear:'ستظهر التجميعات المشتركة هنا عندما يحفظها المستخدمون.', whyWorks:'04 · لماذا يعمل', whyTitle:'لا تحتاج إلى معرفة بالـPC <em>.</em>', whySub:'هدفنا إزالة الحيرة، وليس إضافة ورقة مواصفات أخرى.', outcome:'أخبرنا بالنتيجة التي تريدها.', outcomeSub:'الميزانية ونوع الجهاز والألعاب والتنقل والضوضاء — ما تعرفه يكفي.', protect:'نحمي الميزانية.', protectSub:'هدف 144 FPS هو أرضية، وليس عذرًا لشراء 300 FPS. نتوقف عندما يتحقق الهدف.', tradeoffs:'نوضح التنازلات.', tradeoffsSub:'أفضل قيمة، أسرع أداء، هدوء أو قابلية تطوير — يمكنك تغيير الاتجاه دون إعادة كل شيء.', keepFree:'أبقِه مجانيًا', freeTitle:'صُمم لمساعدتك على الإنفاق بذكاء.', freeSub:'نريد أن يبقى BuildYourPC مفيدًا قبل أن يحتاج إلى الربح.', freeMvp:'نسخة مجانية · جاهزة عالميًا · للهاتف والكمبيوتر', backTop:'العودة للأعلى ↑',
    language:'اللغة', languageTitle:'تحدث بطريقتك.', searchLanguage:'ابحث عن لغة…', marketDock:'السوق', marketTitle:'من أين نشتري؟', searchCountry:'ابحث عن دولة…',
    continueHint:'متابعة', addBudget:'أدخل الميزانية أولًا.', buildFailed:'تعذر إنشاء التجميعة. حاول مرة أخرى.', saved:'تم حفظ التجميعة — تم نسخ الرابط.', saveFailed:'تعذر حفظ التجميعة.', shareFailed:'تعذر إنشاء رابط المشاركة.', linkCopied:'تم نسخ الرابط.', languageSet:'تم اختيار اللغة', languageFallback:'الواجهة تستخدم الإنجليزية حاليًا لهذه اللغة.', marketChanged:'تم اختيار السوق', offline:'تعذر الاتصال بالخادم. تحقق من اتصالك وحاول مرة أخرى.', genericError:'تعذر تنفيذ العملية. حاول مرة أخرى.', budgetRange:'الميزانية خارج النطاق المسموح.', matchReadyText:'النتيجة جاهزة', smart:'الشراء الذكي', speed:'الأداء', beastLabel:'الأقوى', estimatedTotal:'الإجمالي المتوقع', whyFits:'لماذا يناسبك', goalCheck:'تحقق من الهدف', moneyMove:'قرار الميزانية', save:'حفظ', share:'مشاركة', copy:'نسخ الرابط', referenceNote:'بيانات مرجعية — تحقق من الأسعار قبل الشراء.', liveNote:'تظهر الأسعار الحية عند توفرها، وتبقى الأسعار المرجعية موضحة بوضوح.', savedLoaded:'تم تحميل التجميعة المحفوظة.', smartTitle:'الشراء الذكي', speedTitle:'الأداء', beastTitle:'الأقوى', fit:'ملاءمة', viewStore:'فتح المتجر', shareTitle:'تجميعتي على BuildYourPC', shareText:'وجدت هذه التجميعة على BuildYourPC.', chooseBest:'سنحدد الاتجاه الأنسب من إجاباتك التالية.'
  },
  es: {
    continue:'Continuar', matching:'Buscando', skip:'Omitir', back:'Atrás', edit:'Editar', support:'Apoyar', explore:'Explorar', how:'Cómo funciona', results:'Resultados', startBuilding:'Empezar a construir', exploreBuilds:'Explorar equipos', leaveTip:'Dejar propina', buildsCreated:'equipos creados', buildViews:'vistas', shares:'compartidos',
    smarterWay:'Una forma más inteligente de comprar tu próximo ordenador', heroTitle:'Construye el PC que<br><em>realmente necesitas.</em>', heroSub:'Dinos tu presupuesto, tu uso y lo que importa. BuildYourPC encuentra la mejor máquina por tu dinero, no la más cara.',
    livePreview:'VISTA EN DIRECTO', matchingLive:'comparando', yourBudget:'Tu presupuesto', bestFit:'Mejor opción', findSweet:'ENCUENTRA EL PUNTO IDEAL', compareReal:'COMPARA OPCIONES REALES', spendSmarter:'GASTA MEJOR', buildConfidence:'CONSTRUYE CON CONFIANZA',
    discover:'01 · DESCUBRIR', makeEasy:'Hagámoslo fácil.', discoverSub:'Solo hace falta el presupuesto. Todo lo demás afina la recomendación.', stepOf:'Paso {n} de 5', whatLooking:'¿QUÉ ESTAMOS BUSCANDO?', machineTitle:'Elige el tipo de máquina.<br><em>O deja que decidamos.</em>', machineSub:'Puedes cambiarlo después sin empezar de nuevo.', desktop:'PC de sobremesa', desktopSub:'Construir o comprar un PC', laptop:'Portátil', laptopSub:'Gaming y trabajo portátil', prebuilt:'Preensamblado', prebuiltSub:'Listo para usar', custom:'Equipo personalizado', customSub:'Más control, mismo objetivo', used:'Usado / reacondicionado', usedSub:'Aprovecha más el presupuesto', notSure:'No estoy seguro', notSureSub:'Ayúdame a decidir',
    budgetQuestion:'¿CUÁL ES EL PRESUPUESTO?', budgetTitle:'Tu presupuesto es el <em>límite.</em>', budgetSub:'No gastaremos más solo porque haya dinero disponible.', budgetLabel:'Presupuesto', budgetHint:'Siempre puedes ajustar el resultado después.', usingFor:'¿PARA QUÉ LO VAS A USAR?', goalsTitle:'Elige lo que <em>más importa.</em>', optional:'Nada de esto es obligatorio.', gaming:'Gaming', gamingSub:'Quiero que los juegos vayan genial', streaming:'Gaming + streaming', streamingSub:'Jugar y emitir', creation:'Creación', creationSub:'Editar, renderizar y crear', work:'Trabajo + juegos', workSub:'Una máquina para todo', ai:'IA / cálculo', aiSub:'Las cargas locales importan', futureProof:'A prueba de futuro', futureSub:'Que siga siendo útil más tiempo',
    giveMore:'DANOS UN POCO MÁS', tighterMatch:'Solo si quieres una <em>coincidencia más precisa.</em>', skipUnknown:'Omite lo que no sepas.', games:'Juegos', matters:'¿Qué importa?', targetFps:'FPS objetivo', resolution:'Resolución', quiet:'🤫 Silencioso', wifi:'📶 Wi‑Fi', small:'📦 Pequeño', future:'🚀 Futuro', notSureShort:'No estoy seguro', lastCheck:'ÚLTIMA COMPROBACIÓN', ownAnything:'¿Ya tienes <em>algo?</em>', avoidDuplicates:'Evitaremos comprar duplicados.', monitor:'Monitor', ssd:'SSD', ram:'RAM', case:'Caja', psu:'Fuente de alimentación', nothingYet:'Nada todavía', budgetEnough:'El presupuesto es suficiente para empezar.', everythingOptional:'Todo lo demás es opcional.', readyWhen:'Listo cuando tú lo estés.',
    match:'02 · COINCIDENCIA', translated:'Tu dinero, <em>bien aprovechado.</em>', matchSub:'Los resultados se ordenan por ajuste, no solo por rendimiento bruto.', yourBrief:'TU PERFIL', market:'Mercado', direction:'Dirección', smartBuy:'Compra inteligente', speedDemon:'Rendimiento', beast:'La bestia', matchReady:'Resultado listo', value:'Valor', futureScore:'Futuro', fpsEst:'FPS est.', fit:'AJUSTE', live:'DIRECTO', reference:'REF.', marketplace:'MERCADO', viewStore:'Ver tienda',
    exploreSection:'03 · EXPLORAR', exploreTitle:'Equipos de los que vale la pena <em>sacar ideas.</em>', exploreSub:'Los equipos compartidos deben ser útiles, modificables y honestos con los compromisos.', loading:'cargando', loadingBuilds:'Cargando equipos', buildsAppear:'Los equipos compartidos aparecerán aquí.', whyWorks:'04 · POR QUÉ FUNCIONA', whyTitle:'No necesitas conocimientos de PC <em>.</em>', whySub:'La idea es eliminar las dudas, no añadir otra hoja de especificaciones.', outcome:'Tú nos dices el resultado.', outcomeSub:'Presupuesto, tipo de dispositivo, juegos, movilidad, ruido — con eso basta.', protect:'Protegemos el presupuesto.', protectSub:'144 FPS es un objetivo, no una excusa para comprar 300 FPS. Dejamos de gastar cuando ya se cumple.', tradeoffs:'Mostramos los compromisos.', tradeoffsSub:'Mejor valor, más rápido, más silencioso o más ampliable — puedes cambiar de dirección sin rehacer todo.', keepFree:'MANTÉNLO GRATIS', freeTitle:'Creado para ayudarte a gastar mejor.', freeSub:'Queremos que BuildYourPC siga siendo útil antes de necesitar ser rentable.', freeMvp:'MVP gratuito · Global · Móvil + escritorio', backTop:'Volver arriba ↑', language:'IDIOMA', languageTitle:'Habla a tu manera.', searchLanguage:'Buscar idioma…', marketDock:'MERCADO', marketTitle:'¿Dónde compramos?', searchCountry:'Buscar país…',
    continueHint:'Continuar', addBudget:'Añade primero un presupuesto.', buildFailed:'No se pudo crear el equipo. Inténtalo de nuevo.', saved:'Equipo guardado — enlace copiado.', saveFailed:'No se pudo guardar el equipo.', shareFailed:'No se pudo crear el enlace.', linkCopied:'Enlace copiado.', languageSet:'Idioma establecido en', languageFallback:'La interfaz usa inglés como respaldo para este idioma por ahora.', marketChanged:'Mercado cambiado a', offline:'No se pudo conectar con la API. Comprueba la conexión e inténtalo de nuevo.', genericError:'No se pudo completar esta acción. Inténtalo de nuevo.', budgetRange:'El presupuesto debe estar dentro del rango permitido.', matchReadyText:'Resultado listo', smart:'Compra inteligente', speed:'Rendimiento', beastLabel:'La bestia', estimatedTotal:'Total estimado', whyFits:'Por qué encaja', goalCheck:'Comprobación', moneyMove:'Presupuesto', save:'Guardar', share:'Compartir', copy:'Copiar enlace', referenceNote:'Catálogo de referencia — verifica los precios antes de comprar.', liveNote:'Las ofertas en directo se usan cuando están disponibles; los precios de referencia siguen identificados.', savedLoaded:'Equipo guardado cargado.', smartTitle:'Compra inteligente', speedTitle:'Rendimiento', beastTitle:'La bestia', fit:'AJUSTE', viewStore:'Ver tienda', shareTitle:'Mi equipo BuildYourPC', shareText:'Encontré este equipo en BuildYourPC.', chooseBest:'Determinaremos la mejor dirección con tus próximas respuestas.'
  }
};

function t(key, vars={}){ const lang=TRANSLATIONS[state.language]||TRANSLATIONS.en; let text=lang[key]??TRANSLATIONS.en[key]??key; return String(text).replace(/\{(\w+)\}/g,(_,k)=>vars[k]??`{${k}}`); }
function toast(msg){const node=el('toast');node.textContent=msg;node.classList.add('show');clearTimeout(toast._t);toast._t=setTimeout(()=>node.classList.remove('show'),2500)}
function currencyConfig(code){return config.currencies?.[String(code||'USD').toUpperCase()]||config.currencies?.USD||{symbol:String(code||'USD'),locale:undefined,decimalDigits:0,minimum:0,maximum:10000}}
function currencySymbol(code){return currencyConfig(code).symbol || code}
function fmtMoney(value, code=state.currency){
  const cfg=currencyConfig(code); const n=Number(value); if(!Number.isFinite(n)) return '—';
  const languageLocale={en:'en-US',fr:'fr-FR',ar:'ar-MA',es:'es-ES'}[state.language]||cfg.locale||navigator.language;
  try{return new Intl.NumberFormat(languageLocale,{style:'currency',currency:String(code).toUpperCase(),minimumFractionDigits:Number(cfg.decimalDigits??0),maximumFractionDigits:Number(cfg.decimalDigits??0)}).format(n)}catch{return `${currencySymbol(code)}${Math.round(n).toLocaleString(languageLocale)}`}
}
function countryName(code){return config.countries.find(x=>x.code===code)?.name || code}
function updateCountryUI(){el('countryLabel').textContent=state.country;el('budgetCurrency').textContent=state.currency;el('currencySymbol').textContent=currencySymbol(state.currency);el('langBtn').textContent=(config.languages.find(x=>x.code===state.language)?.code||'en').toUpperCase();}
function updateBudgetUI(){const cfg=currencyConfig(state.currency);const min=Number(cfg.minimum||150), max=Number(cfg.maximum||10000);state.budget=Math.min(max,Math.max(min,Number(state.budget)||min));el('budgetInput').min=min;el('budgetInput').max=max;el('budgetInput').step=Number(cfg.decimalDigits||0)>0?'0.01':'1';el('budgetInput').value=Number(state.budget).toLocaleString(undefined,{maximumFractionDigits:Number(cfg.decimalDigits||0)});el('budgetSlider').min=min;el('budgetSlider').max=max;el('budgetSlider').step=Math.max(1,Math.round((max-min)/250));el('budgetSlider').value=Math.min(max,Math.max(min,state.budget));el('heroBudget').textContent=fmtMoney(state.budget);const extra=Math.max(1,Math.round(state.budget*0.07));const title=el('whatIfBudgetTitle');if(title)title.textContent=`${t('smart')}: ${fmtMoney(extra)}`;}

async function readResponse(r){
  const type=(r.headers.get('content-type')||'').toLowerCase();
  const raw=await r.text();
  let data=null;
  if(raw.trim()){
    if(type.includes('application/json') || /^[\[{]/.test(raw.trim())){try{data=JSON.parse(raw)}catch{} }
  }
  if(!r.ok){
    const message=data?.error?.message||data?.error||data?.message||(`${r.status} ${r.statusText}`.trim())||t('genericError');
    const err=new Error(message);err.status=r.status;err.code=data?.error?.code||'HTTP_ERROR';throw err;
  }
  if(!raw.trim()) return {};
  if(data===null){console.error('BuildYourPC API returned a non-JSON success response',{status:r.status,contentType:type,bodyPreview:raw.slice(0,300)});const err=new Error(t('genericError'));err.code='INVALID_JSON_RESPONSE';err.status=r.status;throw err;}
  return data;
}
async function apiFetch(path, options={}){
  let r; try{r=await fetch(API_BASE+path,{...options,headers:{Accept:'application/json',...(options.headers||{})}})}catch(e){const err=new Error(t('offline'));err.code='NETWORK_ERROR';throw err}
  return readResponse(r);
}
function applyTranslations(){
  const set = (selector, key, html=false) => { const n=q(selector); if(n) html ? n.innerHTML=t(key) : n.textContent=t(key); };
  const many = (selector, key) => qa(selector).forEach(n=>n.textContent=t(key));
  set('.desktop-nav a[href="#explore"]','explore'); set('.desktop-nav a[href="#how"]','how'); set('.desktop-nav a[href="#results"]','results');
  set('#startBtn','startBuilding',true); set('#exploreBtn','exploreBuilds'); set('.tip-btn span','leaveTip');
  set('.eyebrow','smarterWay'); set('.hero-copy h1','heroTitle',true); set('.hero-sub','heroSub');
  many('.hero-proof div:nth-child(1) span','buildsCreated'); many('.hero-proof div:nth-child(2) span','buildViews'); many('.hero-proof div:nth-child(3) span','shares');
  set('.tiny-label','livePreview'); set('.status-pill','matchingLive'); many('.preview-bottom .muted','yourBudget'); many('.preview-bottom div:nth-child(2) .muted','bestFit');
  const marquee=[['.marquee-track span:nth-of-type(1)','findSweet'],['.marquee-track span:nth-of-type(2)','compareReal'],['.marquee-track span:nth-of-type(3)','spendSmarter'],['.marquee-track span:nth-of-type(4)','buildConfidence'],['.marquee-track span:nth-of-type(5)','findSweet']]; marquee.forEach(([s,k])=>set(s,k));
  set('#builder .section-kicker','discover'); set('#builder .section-head h2','makeEasy'); set('#builder .section-head p','discoverSub'); set('#skipStep','skip');
  set('[data-step="1"] .step-kicker','whatLooking'); set('[data-step="1"] .step-copy h3','machineTitle',true); set('[data-step="1"] .step-copy p','machineSub');
  const deviceMap={desktop:['desktop','desktopSub'],laptop:['laptop','laptopSub'],prebuilt:['prebuilt','prebuiltSub'],custom:['custom','customSub'],used:['used','usedSub'],not_sure:['notSure','notSureSub']};
  Object.entries(deviceMap).forEach(([d,[k,sb]])=>{const b=q(`[data-device="${d}"]`);if(b){const st=b.querySelector('strong'),sm=b.querySelector('small');if(st)st.textContent=t(k);if(sm)sm.textContent=t(sb)}});
  set('[data-step="2"] .step-kicker','budgetQuestion'); set('[data-step="2"] .step-copy h3','budgetTitle',true); set('[data-step="2"] .step-copy p','budgetSub'); set('#budgetInput','budgetLabel'); const bi=el('budgetInput');if(bi)bi.setAttribute('aria-label',t('budgetLabel'));const bs=el('budgetSlider');if(bs)bs.setAttribute('aria-label',t('budgetLabel'));
  set('.budget-note span:last-child','budgetHint');
  set('[data-step="3"] .step-kicker','usingFor'); set('[data-step="3"] .step-copy h3','goalsTitle',true); set('[data-step="3"] .step-copy p','optional');
  const goalMap={Gaming:['gaming','gamingSub'],Streaming:['streaming','streamingSub'],Creation:['creation','creationSub'],Work:['work','workSub'],AI:['ai','aiSub'],['Future-proof']:['futureProof','futureSub']};Object.entries(goalMap).forEach(([d,[k,sk]])=>{const b=q(`[data-goal="${d}"]`);if(b){const st=b.querySelector('strong'),sm=b.querySelector('small');if(st)st.textContent=t(k);if(sm)sm.textContent=t(sk)}});
  set('[data-step="4"] .step-kicker','giveMore');set('[data-step="4"] .step-copy h3','tighterMatch',true);set('[data-step="4"] .step-copy p','skipUnknown');
  const panels=qa('[data-step="4"] .panel-label');[['games'],['matters'],['targetFps'],['resolution']].forEach(([k],i)=>{if(panels[i])panels[i].textContent=t(k)}); qa('[data-pref="Quiet"]')[0]?.replaceChildren(document.createTextNode(t('quiet'))); qa('[data-pref="Wi-Fi"]')[0]?.replaceChildren(document.createTextNode(t('wifi'))); qa('[data-pref="Small"]')[0]?.replaceChildren(document.createTextNode(t('small'))); qa('[data-pref="Future-proof"]')[0]?.replaceChildren(document.createTextNode(t('future'))); const nr=q('[data-res="smart"]');if(nr)nr.textContent=t('notSureShort');
  set('[data-step="5"] .step-kicker','lastCheck');set('[data-step="5"] .step-copy h3','ownAnything',true);set('[data-step="5"] .step-copy p','avoidDuplicates'); const existing={Monitor:'monitor',SSD:'ssd',RAM:'ram',Case:'case',PSU:'psu',Nothing:'nothingYet'};Object.entries(existing).forEach(([d,k])=>{const st=q(`[data-existing="${d}"] strong`);if(st)st.textContent=t(k)});
  set('#backBtn','back',true); set('#nextBtn','continue',true); set('#builder .wizard-side-note','budgetEnough');
  set('#results .section-kicker','match');set('#results .section-head h2','translated',true);set('#results .section-head p','matchSub');set('.summary-card .tiny-label','yourBrief');set('#editBtn','edit');set('.summary-budget span','budgetLabel');set('.summary-line:nth-of-type(1) span','market');set('.summary-line:nth-of-type(2) span','direction');
  set('.result-title','matchReady'); set('[data-preset="smart"]','smart');set('[data-preset="speed"]','speed');set('[data-preset="beast"]','beast');
  set('[data-whatif="fps"] strong','fpsEst');set('[data-whatif="quiet"] strong','quiet');set('[data-whatif="future"] strong','futureProof');
  set('#explore .section-kicker','exploreSection');set('#explore .section-head h2','exploreTitle',true);set('#explore .section-head p','exploreSub');set('#how .section-kicker','whyWorks');set('#how .section-head h2','whyTitle',true);set('#how .section-head p','whySub');
  const cards=qa('.how-card');[['outcome','outcomeSub'],['protect','protectSub'],['tradeoffs','tradeoffsSub']].forEach(([k,sk],i)=>{if(cards[i]){cards[i].querySelector('h3').textContent=t(k);cards[i].querySelector('p').textContent=t(sk)}});
  set('.tip-large .section-kicker','keepFree');set('.tip-large h2','freeTitle');set('.tip-large p','freeSub');set('.tip-large .primary-btn','leaveTip',true);set('.footer-meta','freeMvp');set('.footer-links a[href="#builder"]','startBuilding');set('.footer-links a[href="#explore"]','explore');set('.footer-links a[href*="ko-fi"]','support');set('.footer-links a[href="#top"]','backTop');
  set('.language-dock .section-kicker','language');set('.language-dock .dock-head h3','languageTitle');set('.country-dock .section-kicker','marketDock');set('.country-dock .dock-head h3','marketTitle');
  const search=el('langSearch');if(search)search.placeholder=t('searchLanguage');const csearch=el('countrySearch');if(csearch)csearch.placeholder=t('searchCountry');
  document.documentElement.lang=state.language; document.documentElement.dir=(config.languages.find(x=>x.code===state.language)?.dir)||(['ar','ur','fa','he'].includes(state.language)?'rtl':'ltr');
  document.title=`BuildYourPC — ${state.language==='ar'?'ابنِ جهازك بذكاء':state.language==='fr'?'Votre argent. Vos besoins. Votre PC.':state.language==='es'?'Tu dinero. Tus necesidades. Tu PC.':'Your money. Your needs. Your PC.'}`;
  const meta=q('meta[name="description"]');if(meta)meta.content=t('heroSub');
  setStep(state.step); updateBudgetUI();
  const brand=q('.brand');if(brand)brand.setAttribute('aria-label', state.language==='ar'?'الصفحة الرئيسية لـ BuildYourPC':'BuildYourPC home');
}


async function loadExistingBuild(){
  const m=location.pathname.match(/^\/build\/([A-Za-z0-9_-]+)$/);
  if(!m) return false;
  try{
    const d=await apiFetch(`/api/builds/${m[1]}`);
    state.result=d.payload;
    renderResults();
    document.getElementById('results').scrollIntoView({behavior:'instant',block:'start'});
    toast(state.language==='ar'?'تم تحميل التجميعة المحفوظة.':state.language==='fr'?'Configuration enregistrée chargée.':'Saved build loaded.');
    return true;
  }catch(e){ console.warn('saved build load failed',e); return false; }
}

async function loadConfig(){
  try{config=await apiFetch('/api/config');}
  catch(e){toast(e.message);config={countries:[{code:'US',name:'United States',currency:'USD'}],languages:[{code:'en',name:'English',native:'English',dir:'ltr'}],games:['Fortnite','Warzone','GTA V','Minecraft'],currencies:{USD:{symbol:'$',locale:'en-US',decimalDigits:0,minimum:150,maximum:10000}},kofi:'https://ko-fi.com/simbawwyy00'}}
  const savedCountry=(()=>{try{return localStorage.getItem('byp_country')}catch{return null}})();
  const savedLanguage=(()=>{try{return localStorage.getItem('byp_language')}catch{return null}})();
  if(savedCountry && config.countries.some(x=>x.code===savedCountry)) state.country=savedCountry;
  const picked=config.countries.find(x=>x.code===state.country); if(picked) state.currency=picked.currency||state.currency;
  if(savedLanguage && config.languages.some(x=>x.code===savedLanguage)) state.language=savedLanguage;
  const lang=config.languages.find(x=>x.code===state.language)||config.languages[0];
  document.documentElement.lang=lang?.code||'en'; document.documentElement.dir=lang?.dir||'ltr';
  updateCountryUI();updateBudgetUI();applyTranslations();renderGames();renderDocks();
}

async function loadExplore(){
  try{
    const d=await apiFetch('/api/explore');
    el('statBuilds').textContent=Number(d.stats.builds||0).toLocaleString();
    el('statViews').textContent=Number(d.stats.views||0).toLocaleString();
    el('statShares').textContent=Number(d.stats.shares||0).toLocaleString();
    const items=[...(d.live||[]),...(d.curated||[])].slice(0,6);
    const box=el('exploreGrid');
    if(!items.length)return;
    box.innerHTML=items.map((x,i)=>{
      const label=x.label||((x.performance_fit||0)>93?'BEST FIT':'BUILD');
      const href=x.id&&x.id!=='reference-sweet-spot'&&x.id!=='reference-quiet'&&x.id!=='reference-fast'?`/build/${x.id}#results`:'#builder';
      const price=x.total!=null?fmtMoney(x.total,x.currency||state.currency):'—';
      return `<a class="explore-card ${i===0?'featured':''} reveal visible" href="${href}"><div class="explore-top"><span class="rank-pill ${i?'muted-pill':''}">${escapeHtml(label)}</span><span>${escapeHtml(x.type||'build')}</span></div><div class="abstract-rig ${i%2?'purple':'violet'}"><div class="abstract-box"></div><div class="abstract-line"></div><div class="abstract-node"></div></div><div class="explore-meta"><div><h3>${escapeHtml(x.title||'Shared build')}</h3><p>${x.views!=null?`${Number(x.views).toLocaleString()} views · ${Number(x.shares||0).toLocaleString()} shares`:'Reference build — starter example.'}</p></div><strong>${price}</strong></div></a>`;
    }).join('');
  }catch(e){ console.warn('explore load failed',e); }
}

function renderGames(){const box=el('gameTags');box.innerHTML='';config.games.slice(0,12).forEach(g=>{const b=document.createElement('button');b.className='tag'+(state.games.includes(g)?' selected':'');b.textContent=g;b.dataset.game=g;b.onclick=()=>{state.games=state.games.includes(g)?state.games.filter(x=>x!==g):[...state.games,g];renderGames();};box.appendChild(b)})}
function renderDocks(){renderLangList(config.languages);renderCountryList(config.countries)}
function renderLangList(list){const box=el('langList');box.innerHTML='';list.forEach(l=>{const b=document.createElement('button');b.className='dock-item'+(state.language===l.code?' active':'');b.innerHTML=`<strong>${escapeHtml(l.native)}</strong><small>${escapeHtml(l.name)}</small>`;b.onclick=()=>{state.language=l.code;try{localStorage.setItem('byp_language',l.code)}catch{};applyTranslations();updateCountryUI();renderLangList(config.languages);closeDocks();const supported=!!TRANSLATIONS[l.code];toast(`${t('languageSet')} ${l.native}${supported?'':` · ${t('languageFallback')}`}`);};box.appendChild(b)})}
function renderCountryList(list){const box=el('countryList');box.innerHTML='';list.forEach(c=>{const b=document.createElement('button');b.className='dock-item'+(state.country===c.code?' active':'');b.innerHTML=`<strong>${c.name}</strong><small>${c.code} · ${c.currency}</small>`;b.onclick=()=>{state.country=c.code;state.currency=c.currency;try{localStorage.setItem('byp_country',c.code)}catch{};updateCountryUI();updateBudgetUI();closeDocks();toast(`${t('marketChanged')} ${c.name}`)};box.appendChild(b)})}
function openDock(which){el('overlay').hidden=false;el(which).hidden=false}
function closeDocks(){el('overlay').hidden=true;el('languageDock').hidden=true;el('countryDock').hidden=true}
function filterDock(inputId,list,render){const term=el(inputId).value.toLowerCase().trim();render(list.filter(x=>`${x.name} ${x.native||''} ${x.code||''}`.toLowerCase().includes(term)))}

function setStep(n){state.step=Math.max(1,Math.min(5,n));qa('.wizard-step').forEach(s=>s.classList.toggle('active',Number(s.dataset.step)===state.step));el('stepLabel').textContent=t('stepOf',{n:state.step});el('progressFill').style.width=`${state.step*20}%`;el('backBtn').disabled=state.step===1;el('wizardNote').textContent=state.step===2?t('budgetEnough'):state.step<5?t('everythingOptional'):t('readyWhen');window.scrollTo({top:document.getElementById('builder').offsetTop-70,behavior:'smooth'})}
function toggleChoice(elm){elm.classList.toggle('selected')}

qa('[data-device]').forEach(b=>b.onclick=()=>{qa('[data-device]').forEach(x=>x.classList.remove('selected'));b.classList.add('selected');state.device_type=b.dataset.device;if(state.device_type==='not_sure')toast(state.language==='ar'?'سنحدد الاتجاه الأنسب من إجاباتك التالية.':state.language==='fr'?'Nous déterminerons la meilleure direction avec vos prochaines réponses.':'We’ll infer the best direction from your next answers.')})
qa('[data-goal]').forEach(b=>b.onclick=()=>{toggleChoice(b);state.use_cases=qa('[data-goal].selected').map(x=>x.dataset.goal)})
qa('[data-existing]').forEach(b=>b.onclick=()=>{b.classList.toggle('selected');state.existing_parts=qa('[data-existing].selected').map(x=>x.dataset.existing)})
qa('[data-pref]').forEach(b=>b.onclick=()=>{b.classList.toggle('selected');state.preferences=qa('[data-pref].selected').map(x=>x.dataset.pref)})
qa('[data-fps]').forEach(b=>b.onclick=()=>{qa('[data-fps]').forEach(x=>x.classList.remove('selected'));b.classList.add('selected');state.target_fps=Number(b.dataset.fps)})
qa('[data-res]').forEach(b=>b.onclick=()=>{qa('[data-res]').forEach(x=>x.classList.remove('selected'));b.classList.add('selected');state.resolution=b.dataset.res==='smart'?null:b.dataset.res})

el('budgetSlider').addEventListener('input',e=>{state.budget=Number(e.target.value);updateBudgetUI()});el('budgetInput').addEventListener('input',e=>{const raw=e.target.value.replace(/,/g,'');const v=Number(raw);if(Number.isFinite(v))state.budget=v;});el('budgetInput').addEventListener('blur',updateBudgetUI);
el('nextBtn').onclick=()=>{if(state.step<5){setStep(state.step+1)}else runRecommendation()};el('backBtn').onclick=()=>setStep(state.step-1);el('skipStep').onclick=()=>state.step<5?setStep(state.step+1):runRecommendation();el('editBtn').onclick=()=>setStep(1);el('startBtn').onclick=()=>document.getElementById('builder').scrollIntoView({behavior:'smooth'});el('exploreBtn').onclick=()=>document.getElementById('explore').scrollIntoView({behavior:'smooth'});
el('langBtn').onclick=()=>openDock('languageDock');el('menuBtn')?.addEventListener('click',()=>{document.body.classList.toggle('menu-open')});el('countryBtn').onclick=()=>openDock('countryDock');el('overlay').onclick=closeDocks;qa('[data-close]').forEach(b=>b.onclick=closeDocks);el('langSearch').oninput=()=>filterDock('langSearch',config.languages,renderLangList);el('countrySearch').oninput=()=>filterDock('countrySearch',config.countries,renderCountryList);

function buildBrief(){const chips=[];chips.push(`${state.device_type==='not_sure'?'Flexible':state.device_type}`);if(state.games.length)chips.push(...state.games.slice(0,3));if(state.target_fps)chips.push(`${state.target_fps}+ FPS`);if(state.resolution)chips.push(state.resolution);if(state.use_cases.length)chips.push(...state.use_cases.slice(0,2));return chips}
async function runRecommendation(){
  const cfg=currencyConfig(state.currency), min=Number(cfg.minimum||150), max=Number(cfg.maximum||10000);
  if(!Number.isFinite(Number(state.budget)) || state.budget<min || state.budget>max){toast(`${t('budgetRange')} ${fmtMoney(min,state.currency)} – ${fmtMoney(max,state.currency)}`);setStep(2);return}
  if(busyActions.has('recommend')) return;
  busyActions.add('recommend'); const btn=el('nextBtn'); btn.disabled=true; btn.innerHTML=t('matching')+' <span>…</span>';
  try{state.result=await apiFetch('/api/recommend',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...state,budget:Number(state.budget),currency:state.currency,country:state.country})});state.preset='smart';renderResults();document.getElementById('results').scrollIntoView({behavior:'smooth'});}
  catch(e){console.error('recommend failed',e);toast(e.message||t('buildFailed'));}
  finally{busyActions.delete('recommend');btn.disabled=false;btn.innerHTML=t('continue')+' <span>→</span>';}
}

function renderResults(){
  const r=state.result;if(!r||!r.query)return;el('summaryBudget').textContent=fmtMoney(r.query.budget,r.query.currency);el('summaryMarket').textContent=`${r.query.country} · ${r.query.currency}`;el('summaryDirection').textContent=r.title;
  el('briefChips').innerHTML=buildBrief().map(x=>`<span class="brief-chip">${escapeHtml(x)}</span>`).join('');
  renderResultPreset(r);
}
function renderResultPreset(result){
  const card=el('resultCard');
  const mode=state.preset||'smart';
  const titleKey=mode==='smart'?'smartTitle':mode==='speed'?'speedTitle':'beastTitle';
  const title=t(titleKey)||result.title;
  const labels={value:t('value'),future:t('futureScore'),fps:t('fpsEst'),fit:t('fit')};
  const offers=(result.parts||[]).flatMap(p=>p.offers||[]).slice(0,6);
  const seenStores=new Set();
  card.innerHTML=`
  <div class="result-hero"><div><span class="section-kicker">${t('matchReady')}</span><h3>${escapeHtml(title)}</h3><p>${escapeHtml(result.tagline||'')}</p><div class="result-metrics"><span>${labels.value} <b>${result.value_score}</b></span><span>${labels.future} <b>${result.future_score}</b></span>${result.fps_estimate?`<span>${labels.fps} <b>${result.fps_estimate.low}–${result.fps_estimate.high}</b></span>`:''}</div></div><div class="score-ring"><div><strong>${result.performance_fit}</strong><span>${labels.fit}</span></div></div></div>
  <div class="parts-grid">${(result.parts||[]).map(p=>`<div class="part-card"><div class="part-top"><span class="part-cat">${escapeHtml(p.category)}</span><span class="part-price">${fmtMoney(p.price,p.currency)}</span></div><h4>${escapeHtml(p.name)}</h4><p>${escapeHtml(p.why)}</p><div class="offers">${(p.offers||[]).slice(0,5).map(o=>{const live=!!o.live; const noPrice=o.price==null; const label=live?t('live'):o.source==='marketplace-search'?t('marketplace'):t('reference'); const meta=o.captured_at?` · ${new Date(o.captured_at).toLocaleDateString()}`:''; return `<a class="offer-link" href="${escapeHtml(o.url)}" target="_blank" rel="noopener noreferrer${o.affiliate_ready?' sponsored':''}"><span class="offer-dot ${live?'on':''}"></span>${escapeHtml(o.store)}${noPrice?'':` · ${fmtMoney(o.price,o.currency)}`} <small class="offer-source">${label}${meta}</small> ${noPrice?`<small class="offer-action">${t('viewStore')}</small>`:'→'}</a>`}).join('')}</div></div>`).join('')}</div>
  <div class="reason-strip">${(result.reasons||[]).slice(0,3).map((x,i)=>`<div class="reason-box"><strong>${[t('whyFits'),t('goalCheck'),t('moneyMove')][i]}</strong>${escapeHtml(x)}</div>`).join('')}</div>
  <div class="build-footer"><div><span class="muted">${t('estimatedTotal')}</span><div class="build-total">${fmtMoney(result.total,result.currency)}</div><small id="dataModeNote" class="data-note"></small></div><div class="build-actions"><button class="small-btn" id="saveBuild">${t('save')}</button><button class="small-btn" id="shareBuild">${t('share')}</button><button class="small-btn" id="copyBuild">${t('copy')}</button></div></div>`;
  qa('.preset-tab').forEach(x=>x.classList.remove('active'));const active=mode==='smart'?q('[data-preset="smart"]'):mode==='speed'?q('[data-preset="speed"]'):q('[data-preset="beast"]');active?.classList.add('active');
  el('heroFit').textContent=`${result.performance_fit}%`;el('heroBudget').textContent=fmtMoney(result.query?.budget ?? state.budget,result.query?.currency || state.currency);
  el('saveBuild').onclick=saveBuild;el('copyBuild').onclick=copyBuild;const shareBtn=el('shareBuild');if(shareBtn)shareBtn.onclick=shareBuild;const dataNote=el('dataModeNote');if(dataNote)dataNote.textContent=result.data_mode==='reference-demo'?t('referenceNote'):t('liveNote');
}

qa('.preset-tab').forEach(b=>b.onclick=()=>{state.preset=b.dataset.preset;const idx=b.dataset.preset==='smart'?0:b.dataset.preset==='speed'?1:2;renderResultPreset(state.result.alternatives[idx]||state.result)});
qa('[data-whatif]').forEach(b=>b.onclick=()=>{if(!state.result)return;const w=b.dataset.whatif;if(w==='500'){const delta=Math.max(50,Math.round(state.budget*0.07));state.budget+=delta;updateBudgetUI();toast(`${t('moneyMove')}: ${fmtMoney(delta)} — ${t('matching').toLowerCase()}…`);runRecommendation()}else if(w==='fps'){state.target_fps=Math.max(144,Number(state.target_fps||60)+60);toast(`${t('fpsEst')}: ${state.target_fps}+`);runRecommendation()}else if(w==='quiet'){if(!state.preferences.includes('Quiet'))state.preferences.push('Quiet');toast(t('quiet'));runRecommendation()}else if(w==='future'){if(!state.preferences.includes('Future-proof'))state.preferences.push('Future-proof');toast(t('futureProof'));runRecommendation()}})

async function saveBuild(){
  if(!state.result||busyActions.has('save'))return; busyActions.add('save'); const b=el('saveBuild'); if(b)b.disabled=true;
  try{const d=await apiFetch('/api/builds',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(state.result)});const url=`${location.origin}${d.url}`;history.replaceState({},'',d.url);try{await navigator.clipboard?.writeText(url)}catch{}toast(t('saved'));}
  catch(e){console.error('save failed',e);toast(e.message||t('saveFailed'));} finally{busyActions.delete('save');if(b)b.disabled=false;}
}
async function copyBuild(){const url=location.href.includes('/build/')?location.href:location.href.split('#')[0]+'#results';try{await navigator.clipboard.writeText(url);toast(t('linkCopied'));}catch(e){toast(url)}}
async function shareBuild(){
  if(!state.result||busyActions.has('share'))return;busyActions.add('share');const b=el('shareBuild');if(b)b.disabled=true;
  try{const d=await apiFetch('/api/builds',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(state.result)});const url=location.origin+d.url;history.replaceState({},'',d.url);try{await apiFetch(`/api/builds/${d.id}/share`,{method:'POST'});}catch(e){console.warn('share metric failed',e)}if(navigator.share)await navigator.share({title:t('shareTitle'),text:t('shareText'),url});else{await navigator.clipboard?.writeText(url);toast(t('linkCopied'));}}
  catch(e){console.error('share failed',e);if(e.name!=='AbortError')toast(e.message||t('shareFailed'));}
  finally{busyActions.delete('share');if(b)b.disabled=false;}
}

function escapeHtml(s){return String(s??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]))}

const observer=new IntersectionObserver(entries=>entries.forEach(e=>{if(e.isIntersecting)e.target.classList.add('visible')}),{threshold:.12});qa('.reveal').forEach(x=>observer.observe(x));

window.addEventListener('hashchange',()=>{if(location.hash==='#results')document.getElementById('results').scrollIntoView({behavior:'smooth'})});
loadConfig().then(()=>{applyTranslations();loadExistingBuild();loadExplore();});
