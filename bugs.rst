- **OK** numéro de tél au format international

- **OK** forcer le téléphone mobile pour la solution de paiement

- le panier ne se vide pas même quand on a fini sa commande, avec ou
  sans confirmation slimpay transmise

  => appel à shop/confirmation au lieu de shop/payment/validate :
  sûrement paramétrage foireux du client slimpay : Return URL

  App ID: hbrkzajxf97b
  App secret: mRlP4N73seC$Lbnrhig%fz%zQ2tR
  Creditor reference: hbrkzajxf97b
  Return URL: http://localhost:8069/shop/payment/validate
  Notification URL: https://vente-directe.commown.fr/test-slimpay


- **OK** téléphone à vérifier : emplacement dans le json corrigé

- insertion de la ligne de paiement

- rapprochement partner-user

- paiement avec un mandat déjà en place

- split prénom nom à mettre dans le formulaire

- créer un module technique "commown"

  * dépendances : payment_slimpay, ecommerce, website_portal_sale, crm

  * réglages :

    + paramètres généraux - Ordre des noms et prénoms des partenaires
      => Firstname,Lastname

    + paramètres généraux - Accès au portail -
      Permettre la réinitialisation du mot de passe depuis la page de connexion
      => cocher

    + paramètres généraux - Accès au portail -
      Autorise les utilisateurs externes à se connecter
      => cocher

    + Administration du site web - eCommerce - Intermédiaires de paiement
      => configurer Slimpay
      => enlever Virement bancaire (i.e. ne plus publier)

    + Ventes - Configuration - Affichage des taxes
      => Afficher les sous-totaux TTC (B2C)
