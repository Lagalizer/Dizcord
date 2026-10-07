=== 1. Bienvenue
# Bienvenue dans Dizcord

Dizcord est un traducteur en temps réel pour Discord et tout autre chat vocal. Il fonctionne entièrement sur
votre PC.

- **Vous entendez les autres dans votre langue.** L'application écoute ce que disent les gens sur Discord, l'écrit,
  le traduit, affiche des sous-titres et peut vous lire la traduction avec une voix naturelle.
- **Ils vous entendent dans leur langue.** Vous parlez dans votre micro. L'application traduit ce que vous avez dit
  et le prononce dans Discord grâce à un câble audio virtuel.
- **Le texte aussi.** Elle traduit les messages Discord dans les serveurs, les messages privés et les fils, tout
  texte que vous surlignez avec la souris, et le texte à l'écran grâce à l'OCR. Vous pouvez aussi écrire dans leur
  langue.
- **Gratuit pour commencer.** Le profil Gratuit, sans clé, marche sans compte et sans paiement. Les moteurs
  payants dans le cloud sont facultatifs.

Ce manuel a douze chapitres. Utilisez les boutons Suivant et Précédent, ou cliquez sur un chapitre dans la liste.
Chaque fois que vous changez de chapitre, le narrateur arrête l'ancien et lit le nouveau. La voix est une voix
naturelle dans la langue de l'application qui tourne sur votre PC. Elle n'a pas besoin d'internet et ne coûte
rien.

=== 2. Premier démarrage
# Premier démarrage

**Étape 1. Ouvrez l'application.** Double-cliquez sur Dizcord.exe, ou sur Dizcord.bat. La première fois,
l'application crée sa propre copie de Python dans son dossier. Cela télécharge environ 750 mégaoctets, prend
quelques minutes et ne demande pas de droits d'administrateur. Rien n'est installé dans Windows.

Ensuite, vous choisissez la langue de l'application. Tout s'affiche dans cette langue, et le guide et ce manuel
sont lus à voix haute dans cette langue. L'application télécharge une fois la voix de cette langue, environ 60
mégaoctets. Puis une courte visite guidée vous montre les premières étapes. Elle ne s'ouvre que cette première
fois ; vous pouvez la revoir depuis cet onglet.

**Étape 2. Installez un câble audio virtuel.** Installez VB-Audio Virtual Cable, qui est gratuit, puis redémarrez
le PC. C'est la seule chose en dehors du dossier, car Windows a besoin d'un pilote pour créer un micro virtuel.

**Étape 3. Réglez Discord.** Ouvrez Discord, puis Paramètres utilisateur, puis Voix et vidéo.

- Périphérique d'entrée : CABLE Output, de VB-Audio Virtual Cable.
- Périphérique de sortie : votre casque.
- Désactivez la Suppression du bruit, la Suppression de l'écho et le Contrôle automatique du gain.

**Étape 4. Réglez l'application.** Choisissez le profil Gratuit, sans clé. Dans l'onglet Sortie, envoyez votre
voix traduite vers CABLE Input. Dans l'onglet Entrée, choisissez le loopback du casque sur lequel Discord joue, et
votre vrai micro. Dans l'onglet Direct, choisissez les langues. Puis appuyez sur Démarrer, ou sur la touche F5.

Le modèle vocal, Whisper small, pèse environ 460 mégaoctets et se télécharge à la première utilisation.

=== 3. La fenêtre principale
# La fenêtre principale

En haut se trouve la case des profils. Un profil garde tous vos réglages de moteurs, de langues et de
périphériques. Vous pouvez enregistrer, enregistrer sous, supprimer, importer et exporter des profils. Les profils
exportés ne contiennent jamais vos clés d'API.

Vos changements sont enregistrés automatiquement environ une seconde après. Vous pouvez désactiver cela dans
l'onglet Paramètres.

À côté de la case des profils, il y a trois boutons :

- **Sous-titres** affiche une fenêtre de sous-titres flottante que vous pouvez déplacer, redimensionner avec la
  molette et régler d'un clic droit.
- **Chat** active la traduction des messages texte de Discord.
- **Démarrer** lance le traducteur vocal. La touche F5 fait la même chose.

Les onglets sont : Tableau de bord, Direct, Texte, Entrée, Sortie, Parole, Traduction, Modèle d'IA, Voix, Clés
d'API, Installation, Paramètres, Manuel et Journal. Les chapitres suivants expliquent ceux que vous utiliserez le
plus.

=== 4. Tableau de bord
# Tableau de bord

Le Tableau de bord est votre poste de commande. C'est le premier onglet, et il montre tout d'un coup d'œil.

- La **carte du traducteur vocal** lance et arrête la traduction vocale en direct, et montre ce qu'il fait :
  reconnaissance, traduction ou parole.
- La **carte de la traduction du chat** lance et arrête la traduction des messages Discord. Elle permet aussi de
  lire à voix haute les messages traduits, l'un après l'autre, ou en laissant un nouveau message interrompre celui
  qui est lu.
- La **carte Vous** sert à indiquer votre nom sur Discord et la langue dans laquelle vous écrivez.
- La **carte des outils** donne accès au surlignage pour traduire, à l'OCR et à la fenêtre des sous-titres.
- La **carte des raccourcis** rappelle vos raccourcis clavier.
- En bas, Dernières traductions montre les dernières phrases traduites.

Les réglages présents à deux endroits, par exemple dans le Tableau de bord et dans l'onglet Texte, restent
toujours synchronisés.

=== 5. Traduction vocale en direct
# Traduction vocale en direct

C'est la fonction principale. Elle marche dans les deux sens, et chaque sens peut être activé séparément.

**Entrant : ils parlent, vous entendez.** L'application écoute le son que Discord joue dans votre casque. Elle
reconnaît la parole, la traduit, affiche des sous-titres et, si vous le voulez, dit la traduction. Vous choisissez
la langue qu'ils parlent, ou Détection automatique.

**Sortant : vous parlez, ils entendent.** L'application écoute votre micro, traduit ce que vous dites et le
prononce dans Discord par le câble virtuel. Votre propre voix n'est pas envoyée à Discord, seulement la traduction.

Dans l'onglet **Direct**, vous réglez les langues des deux sens, regardez les vumètres et lisez la transcription.
Vous pouvez utiliser un bouton appuyer pour parler, et la case Tapez pour parler, où vous tapez une phrase qui est
traduite et dite dans Discord. L'option Répondre dans la langue qu'ils parlent fait suivre à votre langue de sortie
la dernière langue détectée chez l'autre personne.

Dans l'onglet **Entrée**, vous choisissez ce qui est écouté et comment votre micro se déclenche : détection de la
voix, appuyer pour parler ou bascule. Il y a aussi un réglage de sensibilité et une protection contre l'écho, qui
ignore le son capturé pendant que vos propres traductions jouent.

Dans l'onglet **Sortie**, vous choisissez où jouent les traductions, le câble virtuel de votre voix, et le retour
direct avec atténuation. L'atténuation baisse les voix d'origine pendant qu'une traduction est dite, pour que vous
les entendiez encore.

Tous les périphériques audio sont aussi réunis au même endroit, dans l'onglet Paramètres, sous Périphériques audio.

=== 6. Moteurs : parole, traduction, IA et voix
# Moteurs

Chaque étape de la traduction peut utiliser un moteur différent, et vous pouvez en changer à tout moment. Ils sont
enregistrés dans votre profil.

- **Onglet Parole.** Transforme la parole en texte. Le choix gratuit est Whisper, qui tourne sur votre PC. Les
  choix dans le cloud demandent une clé : OpenAI, Groq, Deepgram, ElevenLabs, Azure et Google. Il y a un test du
  micro dans cet onglet.
- **Onglet Traduction.** Le choix gratuit est Google Traduction, sans clé. Les autres sont DeepL, Azure,
  LibreTranslate, MyMemory et le moteur hors ligne Argos. Vous pouvez choisir le ton : naturel, décontracté,
  soutenu ou littéral. Un glossaire fixe la traduction de certains mots, comme des noms ou des termes de jeu.
- **Onglet Modèle d'IA.** Utilisé quand le moteur de traduction est le modèle d'IA. Ce peut être un modèle dans le
  cloud ou un modèle sur votre PC, par exemple avec Ollama ou LM Studio. Vous pouvez ajouter des instructions pour
  l'argot ou les noms.
- **Onglet Voix.** Le moteur qui dit les traductions. Le choix gratuit, ce sont les voix neuronales de Microsoft
  Edge. Piper et Kokoro marchent hors ligne. ElevenLabs, OpenAI, Azure et Google sont payants. Choisissez une voix
  pour chaque sens, ou laissez l'application choisir une voix naturelle pour chaque langue. Pour chaque sens, vous
  pouvez aussi régler la vitesse, la hauteur et le volume de la voix. Ces réglages marchent avec tous les moteurs
  vocaux.

Chaque onglet a un bouton de test, pour vérifier un moteur avant de l'utiliser.

Les profils de départ sont : Gratuit, sans clé. OpenAI. Groq avec Edge. Claude avec ElevenLabs. Et Entièrement
hors ligne, avec Whisper, Ollama et Piper.

=== 7. Clés d'API
# Clés d'API

Les moteurs gratuits n'ont pas besoin de clé. Pour un moteur payant ou dans le cloud, il vous faut une clé d'API
de cette entreprise.

Ouvrez l'onglet **Clés d'API** et collez chaque clé dans sa case. Toutes les clés sont gardées au même endroit,
dans le fichier data, keys point json, dans le dossier de l'application. Les clés ne sont jamais enregistrées dans
les profils, ni incluses quand vous exportez un profil : vous pouvez donc partager vos profils sans risque.

Gardez ce fichier privé. Si vous copiez tout le dossier sur un autre PC, vos clés partent avec.

Les moteurs locaux facultatifs, comme Piper, Kokoro, Argos et les bibliothèques pour cartes graphiques NVIDIA,
s'installent avec install extras point bat, ou avec le bouton Installer maintenant à côté du moteur dans
l'application.

=== 8. Traduire le texte de Discord
# Traduire le texte de Discord

Appuyez sur le bouton **Chat**, ou utilisez la carte du chat dans le Tableau de bord. L'application lit alors les
messages que vous voyez dans l'application Discord, grâce aux fonctions d'accessibilité de Windows, comme un
lecteur d'écran. Elle n'a besoin ni de jeton ni de bot, et n'envoie rien à Discord.

Les nouveaux messages sont traduits et affichés par-dessus le texte d'origine, directement dans Discord, ou dans
une petite fenêtre à côté. Vous choisissez dans l'onglet Texte, sous Afficher les traductions. Cela marche dans les
serveurs, les messages privés, les groupes, les fils et les posts de forum, même avec Discord en arrière-plan. Les
messages déjà dans votre langue, et vos propres messages, sont ignorés. Les traductions ne s'affichent que lorsque
Discord est la fenêtre active, elles ne cachent donc jamais votre jeu.

L'onglet Texte a d'autres outils :

- **Surligner pour traduire.** Sélectionnez du texte, ou double-cliquez sur un mot, et une bulle avec la
  traduction apparaît près de la souris.
- **Ctrl+Alt+T** traduit la sélection en cours dans n'importe quelle application.
- **Ctrl+Alt+Y** remplace ce que vous avez tapé dans la zone de message de Discord par sa traduction dans la langue
  utilisée dans ce chat.
- **Écrire dans leur langue.** Tapez dans l'onglet Texte, puis copiez, collez dans Discord ou envoyez.
- **Ctrl+Alt+O** vous permet de tracer un cadre sur n'importe quelle partie de l'écran. L'application lit le texte
  par OCR et affiche la traduction par-dessus. Cela peut se répéter toutes les quelques secondes.
- **Texte copié.** En option, traduit tout ce que vous copiez.

Vous pouvez modifier tous les raccourcis dans l'onglet Texte. Pour l'OCR d'autres alphabets, comme le russe ou le
japonais, ajoutez cette langue dans les Paramètres de Windows.

=== 9. Sous-titres et transcriptions
# Sous-titres et transcriptions

La **fenêtre des sous-titres** flotte au-dessus de votre jeu ou de Discord. Faites-la glisser pour la déplacer.
Utilisez la molette pour la redimensionner. Faites un clic droit pour les options, comme le nombre de lignes,
l'affichage du texte d'origine et le fond. Dans les Paramètres, vous pouvez changer la taille du texte et la
police.

Chaque conversation peut être enregistrée comme **transcription**. C'est activé par défaut, et vous le désactivez
dans l'onglet Sortie. Les transcriptions sont enregistrées dans le dossier data, sous transcripts, et vous pouvez
ouvrir ce dossier depuis l'onglet Journal ou les Paramètres.

L'onglet Journal montre ce que fait l'application en temps réel. Il a aussi des boutons pour ouvrir les journaux,
les transcriptions et le dossier de l'application. Si quelque chose ne va pas, le journal est le premier endroit
où regarder.

La barre d'état en bas affiche le délai de chaque étape : reconnaissance vocale, traduction et voix, pour voir quel
moteur est lent.

=== 10. Paramètres et mises à jour
# Paramètres et mises à jour

L'onglet **Paramètres** règle la langue de l'application. Après un changement, l'application redémarre dans la
nouvelle langue. Il réunit aussi tous les périphériques audio : ce que l'application écoute, votre micro, où
jouent les traductions et où va votre voix traduite.

Il règle l'apparence de l'application : le thème, sombre ou clair, la police, et la taille du texte de
l'application et des traductions affichées dans Discord, dans la petite fenêtre du chat et dans les bulles. Il
réunit aussi tous les raccourcis, une option pour garder la fenêtre au-dessus des autres, et des boutons pour
réinitialiser la position des fenêtres et ouvrir les dossiers de l'application, des données et des journaux.

L'option Enregistrer les changements automatiquement garde votre profil enregistré environ une seconde après
chaque changement. Elle est activée par défaut.

**Mises à jour.** Appuyez sur Rechercher des mises à jour. Si une version plus récente existe sur GitHub, le bouton
Mettre à jour maintenant apparaît. Il télécharge la nouvelle version et remplace les fichiers du programme. Vos
réglages, profils, clés d'API et modèles téléchargés ne sont jamais touchés. Si la liste des paquets nécessaires a
changé, ils sont aussi mis à jour. À la fin, l'application propose de redémarrer. Elle vérifie aussi discrètement
quelques secondes après son ouverture.

=== 11. Dépannage
# Dépannage

**Lancez l'autotest.** Ouvrez une console dans le dossier de l'application et lancez
`runtime\python.exe tools\selftest.py`. Il joue une phrase de test dans le câble virtuel et teste les deux sens.
S'il finit par le mot PASS, la reconnaissance, la traduction et la voix marchent.

**Personne n'entend ma traduction.** Dans Discord, le périphérique d'entrée doit être CABLE Output. Dans
l'application, l'onglet Sortie doit envoyer vers CABLE Input. Vérifiez que la Suppression du bruit est désactivée
dans Discord.

**L'application n'entend rien.** Dans l'onglet Entrée, vérifiez que le périphérique loopback est celui sur lequel
Discord joue. Regardez les vumètres dans l'onglet Direct. S'ils ne bougent pas, le périphérique n'est pas le bon.

**Ma traduction s'entend deux fois, ou l'application se traduit elle-même.** Activez la protection contre l'écho
dans l'onglet Entrée et portez un casque.

**Un moteur échoue.** Ouvrez l'onglet Journal. Un message qui dit forbidden, ou blocked, veut souvent dire que la
clé ou le modèle n'est pas autorisé pour votre compte. Essayez un autre moteur, puis testez à nouveau.

**La traduction du chat n'affiche rien.** Vérifiez que Discord est la fenêtre active et que le bouton Chat est
activé. La fonction est faite pour l'application Discord pour ordinateur.

**Toujours bloqué.** Lancez l'application avec Dizcord debug point bat. Une console s'ouvre et affiche les erreurs,
ce qui aide quand vous signalez un problème.

=== 12. À propos de ce manuel
# À propos de ce manuel

Vous lisez le manuel intégré à Dizcord. Le narrateur est une voix naturelle dans la langue de l'application. Elle
tourne sur votre PC, marche hors ligne et n'envoie rien nulle part.

- **Suivant et Précédent** changent de chapitre. Le narrateur arrête l'ancien chapitre et commence le nouveau, et le
  nouveau texte s'affiche en même temps.
- **Lire à voix haute** active ou coupe le narrateur. Quand il est coupé, le manuel n'est que du texte.
- **Relire** reprend le chapitre actuel depuis le début.
- **Arrêter** fait taire le narrateur.
- **Voix** et **Vitesse** changent le son. En plus de la voix hors ligne, vous pouvez choisir une voix en ligne, qui
  demande internet, ou l'une des voix de Windows.
- **Revoir la visite guidée** montre de nouveau les premières étapes.

Le narrateur se tait quand vous quittez cet onglet, et il ne démarre jamais tout seul pendant que vous utilisez le
traducteur.

C'est la fin du manuel. Amusez-vous bien avec Dizcord !
