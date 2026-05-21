/* =========================
CURSOR GLOW
========================= */

const glow = document.querySelector(".cursor-glow");

if(glow){

    document.addEventListener("mousemove", (e) => {

        glow.style.left = e.clientX + "px";
        glow.style.top = e.clientY + "px";

    });

}

/* =========================
CARD HOVER EFFECT
========================= */

const cards = document.querySelectorAll(
    ".task-card, .project-card, .stat-card, .operation-card, .mini-analytics-card"
);

cards.forEach((card) => {

    card.addEventListener("mousemove", (e) => {

        const rect = card.getBoundingClientRect();

        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        const moveX = (x - rect.width / 2) / 18;
        const moveY = (y - rect.height / 2) / 18;

        card.style.transform =
            `translateY(-8px) rotateX(${-moveY}deg) rotateY(${moveX}deg)`;

    });

    card.addEventListener("mouseleave", () => {

        card.style.transform =
            "translateY(0px) rotateX(0deg) rotateY(0deg)";

    });

});

/* =========================
COUNTER ANIMATION
========================= */

const counters = document.querySelectorAll(
    ".stat-card h2, .project-card h1, .mini-analytics-card h2"
);

counters.forEach((counter) => {

    const text = counter.innerText;

    if (isNaN(parseInt(text))) return;

    const target = +text.replace("%", "").replace(",", "");

    let count = 0;

    const increment = target / 60;

    const interval = setInterval(() => {

        count += increment;

        if (count >= target) {

            counter.innerText =
                text.includes("%")
                ? target + "%"
                : Math.floor(target).toLocaleString();

            clearInterval(interval);

        } else {

            counter.innerText =
                text.includes("%")
                ? Math.floor(count) + "%"
                : Math.floor(count).toLocaleString();

        }

    }, 20);

});

/* =========================
PAGE FADE
========================= */

document.body.style.opacity = 0;

window.addEventListener("load", () => {

    document.body.style.transition = "1s ease";
    document.body.style.opacity = 1;

});