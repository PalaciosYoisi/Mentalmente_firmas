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
    const serviceList = document.getElementById('servicios-lista');
    
    if (serviceList) {
        const cards = serviceList.querySelectorAll('.service-horizontal-card');

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    cards.forEach((card, i) => {
                        setTimeout(() => {
                            card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
                            card.style.opacity = '1';
                            card.style.transform = 'translateY(0)';
                        }, 200 * (i + 1));
                    });
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.2 });

        observer.observe(serviceList);
    }
});

// =============================================
// NUEVAS FUNCIONALIDADES (sin modificar lo existente)
// =============================================

// 1. Filtrado avanzado para tablas
function setupTableFilters() {
    document.querySelectorAll('.table-filter').forEach(filter => {
        filter.addEventListener('input', function() {
            const tableId = this.dataset.table;
            const columnIndex = parseInt(this.dataset.column);
            const table = document.getElementById(tableId);
            const rows = table.querySelectorAll('tbody tr');
            const filterValue = this.value.toLowerCase();
            
            rows.forEach(row => {
                const cell = row.cells[columnIndex];
                const cellText = cell.textContent.toLowerCase();
                row.style.display = cellText.includes(filterValue) ? '' : 'none';
            });
        });
    });
}

// 2. Ordenamiento de tablas
function setupSortableTables() {
    document.querySelectorAll('.sortable-table th[data-sort]').forEach(header => {
        header.style.cursor = 'pointer';
        header.addEventListener('click', function() {
            const table = this.closest('table');
            const columnIndex = this.cellIndex;
            const sortDirection = this.dataset.sort === 'asc' ? 'desc' : 'asc';
            const rows = Array.from(table.querySelectorAll('tbody tr'));
            
            // Reset all headers
            table.querySelectorAll('th[data-sort]').forEach(h => {
                h.dataset.sort = '';
                h.querySelector('.sort-icon')?.remove();
            });
            
            // Set current header
            this.dataset.sort = sortDirection;
            
            // Add sort icon
            const icon = document.createElement('i');
            icon.className = `fas fa-sort-${sortDirection === 'asc' ? 'up' : 'down'} sort-icon ml-2`;
            this.appendChild(icon);
            
            // Sort rows
            rows.sort((a, b) => {
                const aValue = a.cells[columnIndex].textContent.trim();
                const bValue = b.cells[columnIndex].textContent.trim();
                
                // Numeric sorting
                if (!isNaN(aValue) && !isNaN(bValue)) {
                    return sortDirection === 'asc' ? aValue - bValue : bValue - aValue;
                }
                
                // Date sorting (format: dd/mm/yyyy)
                const dateRegex = /(\d{2})\/(\d{2})\/(\d{4})/;
                if (dateRegex.test(aValue) && dateRegex.test(bValue)) {
                    const aDate = new Date(aValue.replace(dateRegex, '$3-$2-$1'));
                    const bDate = new Date(bValue.replace(dateRegex, '$3-$2-$1'));
                    return sortDirection === 'asc' ? aDate - bDate : bDate - aDate;
                }
                
                // Default string sorting
                return sortDirection === 'asc' 
                    ? aValue.localeCompare(bValue) 
                    : bValue.localeCompare(aValue);
            });
            
            // Re-append sorted rows
            const tbody = table.querySelector('tbody');
            tbody.innerHTML = '';
            rows.forEach(row => tbody.appendChild(row));
        });
    });
}

// 3. Confirmación mejorada para acciones críticas
function setupEnhancedConfirmations() {
    document.querySelectorAll('[data-confirm]').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const message = this.dataset.confirm || '¿Estás seguro de realizar esta acción?';
            const form = this.closest('form');
            
            Swal.fire({
                title: 'Confirmar acción',
                text: message,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#3085d6',
                cancelButtonColor: '#d33',
                confirmButtonText: 'Sí, continuar',
                cancelButtonText: 'Cancelar'
            }).then((result) => {
                if (result.isConfirmed) {
                    if (form) {
                        form.submit();
                    } else if (this.href) {
                        window.location.href = this.href;
                    }
                }
            });
        });
    });
}

// 4. Carga perezosa de imágenes
function setupLazyLoading() {
    if ('IntersectionObserver' in window) {
        const lazyImages = document.querySelectorAll('img.lazy');
        
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    if (img.dataset.srcset) img.srcset = img.dataset.srcset;
                    img.classList.remove('lazy');
                    observer.unobserve(img);
                }
            });
        });
        
        lazyImages.forEach(img => imageObserver.observe(img));
    }
}

// 5. Notificaciones toast personalizadas
function showToast(message, type = 'success') {
    const toastContainer = document.getElementById('toast-container') || createToastContainer();
    const toast = document.createElement('div');
    
    const icons = {
        success: 'check-circle',
        error: 'exclamation-circle',
        warning: 'exclamation-triangle',
        info: 'info-circle'
    };
    
    const colors = {
        success: 'bg-green-500',
        error: 'bg-red-500',
        warning: 'bg-yellow-500',
        info: 'bg-blue-500'
    };
    
    toast.className = `toast ${colors[type]} text-white rounded-lg shadow-lg mb-2 overflow-hidden`;
    toast.innerHTML = `
        <div class="flex items-center p-4">
            <i class="fas fa-${icons[type]} mr-3"></i>
            <span>${message}</span>
            <button class="ml-auto toast-close">
                <i class="fas fa-times"></i>
            </button>
        </div>
        <div class="toast-progress h-1 bg-white bg-opacity-30 w-full"></div>
    `;
    
    toastContainer.appendChild(toast);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        toast.classList.add('fade-out');
        setTimeout(() => toast.remove(), 300);
    }, 5000);
    
    // Manual close
    toast.querySelector('.toast-close').addEventListener('click', () => {
        toast.classList.add('fade-out');
        setTimeout(() => toast.remove(), 300);
    });
    
    // Progress bar animation
    toast.querySelector('.toast-progress').style.animation = 'progress 5s linear forwards';
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'fixed bottom-4 right-4 z-50 w-full max-w-xs space-y-2';
    document.body.appendChild(container);
    return container;
}

// 6. Inicialización de todas las nuevas funcionalidades
document.addEventListener('DOMContentLoaded', function() {
    setupTableFilters();
    setupSortableTables();
    setupEnhancedConfirmations();
    setupLazyLoading();
    
    // Añadir estilos para la animación de la barra de progreso
    const style = document.createElement('style');
    style.textContent = `
        @keyframes progress {
            from { width: 100%; }
            to { width: 0%; }
        }
        .toast {
            transition: transform 0.3s ease, opacity 0.3s ease;
        }
        .fade-out {
            transform: translateX(100%);
            opacity: 0;
        }
    `;
    document.head.appendChild(style);
});

// =============================================
// FUNCIONES EXISTENTES (se mantienen igual)
// =============================================
// [El contenido existente de main.js se mantiene aquí sin cambios]