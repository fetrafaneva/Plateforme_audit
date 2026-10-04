import { defineStore } from "pinia";
import api from "../services/api";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    token: localStorage.getItem("token") || null,
    utilisateur: null,
  }),
  getters: {
    estConnecte: (state) => !!state.token,
  },
  actions: {
    async login(email, motDePasse) {
      const { data } = await api.post("/auth/login", {
        email,
        mot_de_passe: motDePasse,
      });
      this.token = data.access_token;
      localStorage.setItem("token", this.token);
      await this.chargerUtilisateur();
    },
    async chargerUtilisateur() {
      const { data } = await api.get("/auth/me");
      this.utilisateur = data;
    },
    deconnexion() {
      this.token = null;
      this.utilisateur = null;
      localStorage.removeItem("token");
    },
  },
});
