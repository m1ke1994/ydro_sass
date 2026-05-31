from telegram_logs.management.commands.run_telegram_polling import Command as PollingCommand


class Command(PollingCommand):
    help = "Alias for run_telegram_polling."
