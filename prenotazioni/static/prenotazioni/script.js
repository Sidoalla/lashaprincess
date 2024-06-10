document.addEventListener('DOMContentLoaded', function() {
    var calendarEl = document.getElementById('calendar');
    var selectedDate = null;
    var selectedTime = null;
    var userName = null;
    var userEmail = null;
    var selectedTipo = new URLSearchParams(window.location.search).get('artist'); // Assicurati che 'artist' corrisponda al parametro nella query string
    var tooltip = document.getElementById('tooltip');
    var clickTimeout = null;
    var doubleClick = false;
    var isAdmin = document.body.dataset.isAdmin === 'True';

    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        initialDate: new Date(),
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,dayGridWeek,dayGridDay'
        },
        events: '/get_events/',
        dateClick: function(info) {
            if (clickTimeout) {
                clearTimeout(clickTimeout);
                clickTimeout = null;
                doubleClick = true;
                handleDateDoubleClick(info);
            } else {
                clickTimeout = setTimeout(function() {
                    if (!doubleClick) {
                        handleDateClick(info);
                    }
                    doubleClick = false;
                    clickTimeout = null;
                }, 300);
            }
        },
        eventMouseEnter: function(info) {
            var event = info.event;
            var tooltipContent = `
                <div><strong>${event.title}</strong></div>
                <div>${event.start.toLocaleString()}</div>
            `;
            tooltip.innerHTML = tooltipContent;
            tooltip.style.display = 'block';
            tooltip.style.top = (info.jsEvent.pageY + 10) + 'px';
            tooltip.style.left = (info.jsEvent.pageX + 10) + 'px';
        },
        eventMouseLeave: function(info) {
            tooltip.style.display = 'none';
        },
        editable: isAdmin,
        eventClick: function(info) {
            if (isAdmin) {
                var deleteButton = document.createElement('button');
                deleteButton.classList.add('delete-button');
                deleteButton.innerHTML = '&times;';
                deleteButton.onclick = function() {
                    openReasonModal(info.event);
                };
                info.el.appendChild(deleteButton);
            }

            if (clickTimeout) {
                clearTimeout(clickTimeout);
                clickTimeout = null;
                doubleClick = true;
                handleEventDoubleClick(info);
            } else {
                clickTimeout = setTimeout(function() {
                    if (!doubleClick) {
                        handleEventClick(info);
                    }
                    doubleClick = false;
                    clickTimeout = null;
                }, 300);
            }
        },
        eventDrop: function(info) {
            if (isAdmin) {
                handleEventDrop(info);
            } else {
                info.revert();
            }
        }
    });
    calendar.render();

    // Funzione per aggiornare il calendario
    function updateCalendar() {
        calendar.refetchEvents();
    }

    // Esegui l'aggiornamento ogni 30 secondi (30000 millisecondi)
    setInterval(updateCalendar, 30000);

    function handleDateClick(info) {
        selectedDate = info.dateStr;
        fetch(`/get_events/?date=${selectedDate}`)
            .then(response => response.json())
            .then(data => {
                if (data.length >= 3) {
                    alert('Numero massimo di prenotazioni raggiunto per questo giorno.');
                } else {
                    document.getElementById('modal-overlay').style.display = 'block';
                    document.getElementById('time-selection-modal').style.display = 'block';
                    generateTimeOptions(data);
                }
            });
    }

    function handleDateDoubleClick(info) {
        if (isAdmin) {
            var events = calendar.getEvents();
            events.forEach(function(event) {
                if (event.startStr === info.dateStr) {
                    event.setProp('classNames', ['shake']);
                }
            });
            setTimeout(function() {
                events.forEach(function(event) {
                    if (event.startStr === info.dateStr) {
                        event.setProp('classNames', []);
                    }
                });
            }, 2000);
        } else {
            document.getElementById('login-modal').style.display = 'block';
        }
    }

    function handleEventClick(info) {
        var event = info.event;
        var tooltipContent = `
            <div><strong>${event.title}</strong></div>
            <div>${event.start.toLocaleString()}</div>
        `;
        tooltip.innerHTML = tooltipContent;
        tooltip.style.display = 'block';
        tooltip.style.top = (info.jsEvent.pageY + 10) + 'px';
        tooltip.style.left = (info.jsEvent.pageX + 10) + 'px';
    }

    function handleEventDoubleClick(info) {
        if (isAdmin) {
            openEditModal(info.event);
        } else {
            document.getElementById('login-modal').style.display = 'block';
        }
    }

    function handleEventDrop(info) {
        if (isAdmin) {
            var confirmed = confirm('Vuoi spostare questa prenotazione?');
            if (confirmed) {
                updateEvent(info.event);
            } else {
                info.revert();
            }
        } else {
            alert('Non hai i permessi per modificare o cancellare questa prenotazione.');
            info.revert();
        }
    }

    function openEditModal(event) {
        var modal = document.getElementById('edit-modal');
        var eventId = event.id;
        modal.querySelector('#event-id').value = eventId;
        modal.querySelector('#event-title').value = event.title;
        modal.querySelector('#event-start').value = event.start.toISOString().slice(0, 16);
        modal.querySelector('#event-end').value = event.end ? event.end.toISOString().slice(0, 16) : '';
        modal.style.display = 'block';
    }

    function closeEditModal() {
        var modal = document.getElementById('edit-modal');
        modal.style.display = 'none';
    }

    function updateBooking() {
        var eventId = document.getElementById('event-id').value;
        var eventTitle = document.getElementById('event-title').value;
        var eventStart = document.getElementById('event-start').value;
        var eventEnd = document.getElementById('event-end').value;

        fetch(`/modifica_prenotazione/${eventId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                data_prenotazione: eventStart.split('T')[0],
                ora_prenotazione: eventStart.split('T')[1].substring(0, 5)
            })
        }).then(response => {
            if (response.ok) {
                alert('Prenotazione aggiornata con successo.');
                var event = calendar.getEventById(eventId);
                event.setProp('title', eventTitle);
                event.setStart(eventStart);
                event.setEnd(eventEnd || null);
                closeEditModal();
            } else {
                alert('Errore durante l\'aggiornamento della prenotazione.');
            }
        });
    }

    function deleteEvent(event, reason) {
        if (!event.id) {
            alert('ID evento non trovato.');
            return;
        }

        fetch(`/cancella_prenotazione/${event.id}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ motivo: reason })
        }).then(response => {
            if (response.ok) {
                alert('Prenotazione eliminata con successo.');
                event.remove();
                updateCalendar();
            } else {
                alert('Errore durante l\'eliminazione della prenotazione.');
            }
        });
    }
    
    function openReasonModal(event) {
        var modal = document.getElementById('reason-modal');
        modal.querySelector('#reason-event-id').value = event.id;
        modal.style.display = 'block';
    }
    
    function submitReason() {
        var modal = document.getElementById('reason-modal');
        var reason = modal.querySelector('#cancellation-reason').value;
        var eventId = modal.querySelector('#reason-event-id').value;
    
        if (reason) {
            var event = calendar.getEventById(eventId);
            deleteEvent(event, reason);
            closeReasonModal();
        } else {
            alert('Inserisci il motivo per la cancellazione.');
        }
    }

    function generateTimeOptions(events) {
        var ul = document.getElementById('time-list');
        ul.innerHTML = '';
        var startTime = 9.5;
        var endTime = 18.5;
        var allTimes = [];
        for (var hour = startTime; hour <= endTime; hour += 0.5) {
            var hourPart = Math.floor(hour);
            var minutePart = (hour % 1) * 60;
            var label = ('0' + hourPart).slice(-2) + ':' + ('0' + minutePart).slice(-2);
            allTimes.push(label);
        }

        var bookedTimes = events.map(event => {
            var date = new Date(event.start);
            return date.getHours() + date.getMinutes() / 60;
        });

        allTimes.forEach(time => {
            var isAvailable = bookedTimes.every(bookedTime => {
                var selectedHour = parseInt(time.split(':')[0]);
                var selectedMinute = parseInt(time.split(':')[1]);
                var selectedTimeInHours = selectedHour + selectedMinute / 60;

                return bookedTimes.every(bookedTime => {
                    var timeDiff = Math.abs(selectedTimeInHours - bookedTime);
                    return timeDiff >= 3;
                });
            });

            var li = document.createElement('li');
            li.classList.add('list-group-item', 'list-group-item-action');
            if (!isAvailable) {
                li.classList.add('unavailable');
                li.onclick = function() {
                    alert('L\'orario selezionato è già prenotato o troppo vicino a un altro appuntamento. Scegli un altro orario.');
                };
            } else {
                li.onclick = function() {
                    var siblings = ul.children;
                    for (var i = 0; i < siblings.length; i++) {
                        siblings[i].classList.remove('active');
                    }
                    this.classList.add('active');
                    selectedTime = this.textContent;
                    showSummaryModal();
                };
            }
            li.textContent = time;
            ul.appendChild(li);
        });
    }

    function showSummaryModal() {
        userName = prompt("Inserisci il tuo nome:");
        userEmail = prompt("Inserisci la tua email:");
        if (userName && userEmail) {
            var summary = `Nome: ${userName}<br>Email: ${userEmail}<br>Data: ${selectedDate}<br>Ora: ${selectedTime}<br>Tipo: ${selectedTipo}`;
            document.getElementById('summary-content').innerHTML = summary;
            document.getElementById('modal-overlay').style.display = 'none';
            document.getElementById('time-selection-modal').style.display = 'none';
            document.getElementById('summary-modal-overlay').style.display = 'block';
            document.getElementById('summary-modal').style.display = 'block';
        } else {
            closeModal();
        }
    }

    function closeSummaryModal() {
        document.getElementById('summary-modal-overlay').style.display = 'none';
        document.getElementById('summary-modal').style.display = 'none';
        closeModal();
    }

    function confirmBooking() {
        var emailConsent = document.getElementById('email-consent').checked;

        if (userName && userEmail && selectedDate && selectedTime && selectedTipo) {
            fetch('/aggiungi_prenotazione/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    nome: userName,
                    email: userEmail,
                    data_prenotazione: selectedDate,
                    ora_prenotazione: selectedTime,
                    tipo: selectedTipo,
                    email_consent: emailConsent
                })
            }).then(response => {
                return response.json().then(data => {
                    if (response.ok) {
                        calendar.addEvent({
                            title: `Prenotazione di ${userName} (${selectedTipo})`,
                            start: `${selectedDate}T${selectedTime}`,
                            allDay: false
                        });
                        closeSummaryModal();
                    } else {
                        alert(data.message || 'Errore durante la prenotazione.');
                        closeSummaryModal();
                    }
                });
            }).catch(error => {
                console.error('Error:', error);
                closeSummaryModal();
            });
        } else {
            alert('Tutti i campi sono obbligatori.');
            closeSummaryModal();
        }
    }

    function closeModal() {
        document.getElementById('modal-overlay').style.display = 'none';
        document.getElementById('time-selection-modal').style.display = 'none';
        selectedTime = null;
        updateCalendar();
    }

    function closeLoginModal() {
        document.getElementById('login-modal').style.display = 'none';
    }

    function closeReasonModal() {
        var modal = document.getElementById('reason-modal');
        modal.style.display = 'none';
    }

    window.closeModal = closeModal;
    window.closeSummaryModal = closeSummaryModal;
    window.confirmBooking = confirmBooking;
    window.closeLoginModal = closeLoginModal;
    window.closeReasonModal = closeReasonModal;
    window.submitReason = submitReason;
    window.closeEditModal = closeEditModal;
    window.updateBooking = updateBooking;

    function getCookie(name) {
        const nameEQ = name + "=";
        const ca = document.cookie.split(';');
        for (let i = 0; i < ca.length; i++) {
            let c = ca[i];
            while (c.charAt(0) === ' ') c = c.substring(1, c.length);
            if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
        }
        return null;
    }
});
