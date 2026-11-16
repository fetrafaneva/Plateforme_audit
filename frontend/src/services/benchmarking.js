import api from "./api";

const data = (res) => res.data;

// Périodes déjà calculées (auditeur, administrateur, responsable hiérarchique)
export const listerPeriodes = () => api.get("/benchmarking/periodes").then(data);

// Clôture d'une période : recalcule la photographie et les synthèses (auditeur, administrateur)
export const calculerPeriode = (periode) =>
  api.post("/benchmarking/calculer", null, { params: { periode } }).then(data);

// Classement complet d'une période (auditeur, administrateur)
export const obtenirClassement = (params = {}) =>
  api.get("/benchmarking/", { params }).then(data);

// Position du service de l'utilisateur, sans nommer les autres services
export const obtenirMonBenchmark = (params = {}) =>
  api.get("/benchmarking/mon-service", { params }).then(data);

// Synthèses d'audit générées pour une période (auditeur, administrateur)
export const listerRapportsAudit = (params = {}) =>
  api.get("/benchmarking/rapports", { params }).then(data);
