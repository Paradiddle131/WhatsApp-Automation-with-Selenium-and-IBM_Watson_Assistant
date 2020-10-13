import time
from whatsapp import WhatsApp

if __name__ == '__main__':
    wa = WhatsApp(100, session="mysession")

    name = 'name of the recipient/group'

    # print("\n\n\n @@@ #of PARTICIPANTS: ", wa.participants_count_for_group(name), "\n\n\n")

    # list_participants = wa.get_group_participants(name)
    # print(f"\n\n\n @@@ {len(list_participants)} PARTICIPANTS: ", list_participants, "\n\n\n")

    print(f"\n\n\n @@@ MESSAGES OF GROUP '{name}':\n ", wa.get_messages(name), "\n\n\n")
    time.sleep(7)
    wa.quit()