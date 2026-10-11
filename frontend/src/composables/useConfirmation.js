import { reactive } from "vue";

// État partagé : une seule fenêtre de confirmation à la fois, affichée par
// <ConfirmDialog /> (monté une fois dans App.vue).
export const etatConfirmation = reactive({
  ouvert: false,
  titre: "",
  message: "",
  libelleConfirmer: "Confirmer",
  libelleAnnuler: "Annuler",
  danger: false,
});

let resoudre = null;

/**
 * Ouvre la fenêtre de confirmation et renvoie une promesse :
 * true si l'utilisateur confirme, false s'il annule (bouton, Échap ou clic à côté).
 *
 *   if (!(await confirmer({ titre: "Supprimer", message: "...", danger: true }))) return;
 */
export function confirmer({
  titre = "Confirmation",
  message = "",
  libelleConfirmer = "Confirmer",
  libelleAnnuler = "Annuler",
  danger = false,
} = {}) {
  if (resoudre) resoudre(false); // une confirmation déjà ouverte est annulée
  Object.assign(etatConfirmation, {
    ouvert: true,
    titre,
    message,
    libelleConfirmer,
    libelleAnnuler,
    danger,
  });
  return new Promise((resolve) => {
    resoudre = resolve;
  });
}

export function repondre(valeur) {
  etatConfirmation.ouvert = false;
  if (resoudre) {
    resoudre(valeur);
    resoudre = null;
  }
}
