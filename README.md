
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

