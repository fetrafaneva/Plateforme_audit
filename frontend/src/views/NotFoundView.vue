<template>
  <div>
    <header class="hero hero-compact">
      <div class="container">
        <p class="eyebrow" style="color: #fff; opacity: 0.85">Erreur 404</p>
        <h1>Page introuvable</h1>
        <p class="hero-meta">
          L'adresse demandée n'existe pas ou a été déplacée.
        </p>
      </div>
    </header>
    <main class="container page">
      <section class="card" style="text-align: center">
        <p class="muted">Vérifie l'adresse, ou retourne à une page connue.</p>
        <RouterLink to="/dashboard" class="btn btn-primary btn-sm"
          >Tableau de bord</RouterLink
        >
      </section>
    </main>
  </div>
</template>
