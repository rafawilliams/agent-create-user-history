# Títulos de evaluación de modelos

Propuesta de 5 títulos de ejemplo para evaluar a Claude Sonnet y a Amazon Titan (US7.1). Son inventados: no contienen datos reales de personas ni de la empresa.

Cada título es una línea que empieza con un guion y un espacio. El comando exige exactamente 5. Para aprobarlos, revisa que sigan siendo inventados y ejecuta desde `backend/`:

    python -m story_service.evaluate_models approve

Eso agrega al final la línea `aprobado: <huella>`. Si cambias un título, hay que aprobar otra vez.

- Recuperar la contraseña de mi cuenta
- Exportar el listado de pedidos a una hoja de cálculo
- Recibir un aviso cuando un envío se retrasa
- Filtrar los productos por rango de precio
- Cancelar una reserva antes de la fecha de entrada
