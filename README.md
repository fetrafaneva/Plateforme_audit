
Un simple journal d'accès (qui a consulté quoi, quand) ne suffit pas à protéger des données sensibles comme l'état civil ou les dossiers d'identité au sein d'une administration décentralisée : il faut aussi pouvoir détecter les comportements anormaux (un agent qui consulte soudainement 200 dossiers en une heure, ou en dehors de sa zone géographique habituelle), garantir que ce journal ne peut être trafiqué a posteriori, et comparer objectivement les pratiques entre communes/services pour identifier celles qui présentent un profil de risque plus élevé. C'est la combinaison de trois exigences — intégrité cryptographique, analyse comportementale statistique, et benchmarking inter-services — qui rend ce sujet à la fois un vrai défi de sécurité logicielle et un vrai terrain d'analyse de données.

Objectif général

Concevoir une plateforme d'audit qui garantit l'intégrité inviolable des journaux d'accès aux données sensibles, détecte les comportements anormaux par analyse statistique, et permet une comparaison objective des pratiques entre services et communes.

Objectifs spécifiques
Journaliser chaque accès à une donnée sensible dans un registre chaîné cryptographiquement (infalsifiable)
Construire un profil comportemental normal (baseline) pour chaque agent et chaque service
Détecter statistiquement les écarts significatifs par rapport à ce profil
Comparer les patterns d'accès entre communes/services pour identifier les profils de risque atypiques
Restituer les résultats via des rapports d'audit exploitables et des explications compréhensibles
Fonctionnalités principales
Authentification et gestion des rôles/permissions par service
Journalisation automatique de chaque accès (chaînage cryptographique SHA-256 entre entrées)
Vérification d'intégrité du journal (détection de toute tentative de modification a posteriori)
Construction d'un profil comportemental statistique par agent (volume, horaires, périmètre habituel d'accès)
Détection d'anomalies par écart au profil (contrôle statistique type carte de contrôle, z-score)
Score de risque calculé pour chaque événement d'accès
Alertes en temps réel en cas de dépassement de seuil
Ouverture et suivi d'investigations sur les cas suspects (workflow d'enquête interne)
Benchmarking comparatif entre communes/services (quel service a le profil de risque le plus atypique, et pourquoi)
Tableau de bord narratif expliquant automatiquement les causes probables d'une alerte
Génération de rapports de conformité réglementaire périodiques
Simulation "et si" : impact estimé d'un renforcement des contrôles sur un service donné
Nombre de tables : 12

utilisateurs, roles_permissions, services_communes, ressources_sensibles, journal_acces (chaîné cryptographiquement), profils_comportementaux, scores_anomalie, alertes_securite, investigations, rapports_audit, politiques_conformite, benchmarking_services

Architecture technique
PostgreSQL pour la persistance transactionnelle (utilisateurs, journal, résultats d'analyse)
Module de chaînage cryptographique (Node.js ou Python, hash SHA-256 liant chaque entrée du journal à la précédente) pour garantir l'infalsifiabilité — cœur "sécurité" du sujet
Python (pandas, statsmodels, scipy) pour la construction des profils comportementaux et la détection statistique d'anomalies — cœur "analyse de données" du sujet, qui correspond directement à ton point fort
Streamlit ou React pour le tableau de bord : Streamlit permet de concentrer ton temps sur l'analyse plutôt que sur le développement d'interface, ce qui est cohérent avec un profil orienté data
Architecture volontairement sobre côté infrastructure (pas de microservices, pas de streaming) pour que la complexité reste concentrée là où tu es le plus à l'aise : la rigueur analytique
Partie innovante

Le sujet combine une brique d'ingénierie de sécurité (intégrité inviolable du journal, un vrai problème d'ingénierie logicielle) avec une brique d'analyse comportementale statistique (établir une baseline, détecter un écart significatif, éviter les faux positifs) et une brique de data storytelling comparatif (pourquoi telle commune a un profil différent, avec quelle robustesse statistique). C'est cette dimension analytique poussée — pas juste "on détecte une anomalie" mais "on explique pourquoi, avec quelle méthode, et quelles réserves" — qui distingue ce sujet élargi d'un simple système de logs sécurisés.

Méthodologie

UML et modélisation de menaces pour la partie sécurité ; démarche statistique rigoureuse (définition de la baseline, choix du seuil de détection, contrôle du taux de faux positifs) pour la partie analytique ; Scrum pour le développement applicatif.

Évaluation
Sécurité : résistance du journal à des tentatives de falsification simulées
Détection d'anomalies : précision/rappel sur des comportements anormaux injectés artificiellement dans un jeu de données simulé, taux de faux positifs
Benchmarking : cohérence et robustesse des comparaisons entre services (stabilité des résultats sur des sous-échantillons différents)
Utilité perçue : clarté des explications narratives testée auprès d'un utilisateur simulant un auditeur ou un responsable hiérarchique
Niveau de difficulté

Très difficile — la difficulté est répartie entre une brique de sécurité logicielle (chaînage cryptographique) et une brique de rigueur statistique (baseline, seuils, faux positifs), ce qui donne un mémoire riche sur deux plans complémentaires.

Faisabilité solo (stage)

Bonne à très bonne : chaque brique prise isolément est bien maîtrisable (le chaînage cryptographique est une implémentation classique bien documentée ; l'analyse statistique s'appuie sur des méthodes éprouvées). Le risque principal est de vouloir aller trop loin sur le machine learning avancé pour la détection — recommandé de rester sur des méthodes statistiques simples et bien justifiées plutôt que sur des modèles complexes moins interprétables.

Intérêt pour un jury de Master 2

9/10 — le sujet initial (sécurité/intégrité) était déjà solide ; l'élargissement vers l'analyse comportementale et le benchmarking ajoute une vraie profondeur data science, ce qui permet de démontrer un profil complet (ingénierie + analyse), tout en restant clairement délimité et réalisable en stage.
