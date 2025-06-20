// Función para inicializar el signature pad
function initSignaturePad(canvasId, clearBtnId, hiddenInputId) {
    const canvas = document.getElementById(canvasId);
    const signaturePad = new SignaturePad(canvas, {
        backgroundColor: 'rgb(255, 255, 255)',
        penColor: 'rgb(0, 0, 0)'
    });
    
    // Ajustar canvas al tamaño del contenedor
    function resizeCanvas() {
        const ratio = Math.max(window.devicePixelRatio || 1, 1);
        canvas.width = canvas.offsetWidth * ratio;
        canvas.height = canvas.offsetHeight * ratio;
        canvas.getContext('2d').scale(ratio, ratio);
        signaturePad.clear();
    }
    
    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();
    
    // Limpiar firma
    document.getElementById(clearBtnId).addEventListener('click', function() {
        signaturePad.clear();
    });
    
    // Guardar firma antes de enviar formulario
    if (hiddenInputId) {
        const form = document.querySelector('form');
        if (form) {
            form.addEventListener('submit', function(event) {
                if (signaturePad.isEmpty()) {
                    event.preventDefault();
                    alert("Por favor proporcione su firma antes de enviar.");
                } else {
                    document.getElementById(hiddenInputId).value = signaturePad.toDataURL('image/png');
                }
            });
        }
    }
    
    return signaturePad;
}

// Inicializar tooltips de Bootstrap
document.addEventListener('DOMContentLoaded', function() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Animaciones de entrada con Intersection Observer
function animateOnScroll() {
    const fadeEls = document.querySelectorAll('.fade-in');
    const slideEls = document.querySelectorAll('.slide-in');
    const options = {
        threshold: 0.15
    };
    const fadeObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = 1;
                entry.target.style.transform = 'none';
                entry.target.style.transition = 'opacity 1s, transform 1s';
                observer.unobserve(entry.target);
            }
        });
    }, options);
    fadeEls.forEach(el => {
        el.style.opacity = 0;
        el.style.transform = 'translateY(40px)';
        fadeObserver.observe(el);
    });
    const slideObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = 1;
                entry.target.style.transform = 'none';
                entry.target.style.transition = 'opacity 1s, transform 1s';
                observer.unobserve(entry.target);
            }
        });
    }, options);
    slideEls.forEach(el => {
        el.style.opacity = 0;
        el.style.transform = 'translateX(-40px)';
        slideObserver.observe(el);
    });
}
document.addEventListener('DOMContentLoaded', animateOnScroll);

// Animación secuencial de tarjetas de servicios
window.addEventListener('DOMContentLoaded', function() {
    const cards = document.querySelectorAll('.service-horizontal-card');
    cards.forEach((card, i) => {
        setTimeout(() => {
            card.style.opacity = 1;
            card.style.transform = 'translateY(0)';
        }, 200 * i);
    });
});