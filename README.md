# mail-attachments-archiver
Store mail attachments to file-system

### Description ###

This program is a simple mail client written in Python.

The program will automatically archive email attachments based on predefined rules.

### Installation ###

Clone the repository:

```
git clone https://github.com/johnbenclark/mail-attachments-archiver.git
```

### Configuration ###

Create two files, `imap.json` and `config.json` and specify their location with the appropriate command-line flags.

#### IMAP Connection Setup ####

Example `imap.json`:
```
{
	"server": "imap.yourprovider.com",
	"user": "you@yourprovider.com",
	"password": "PASSWORD"
}
```

All of the following keys are required:
* `server`: adopted IMAP server (e.g. `imap.gmail.com`)
* `user`: adopted IMAP username (e.g. `username@gmail.com`)
* `password`: adopted IMAP password 

#### Behavior Configuration ####

The behavior of the program has configurations for each mapping as well as general configuration.

Example `config.json`:
```
{
	"mappings": [
		{
			"filter_sender": true,
			"senders": [
				"bob@hisprovider.com"
			],
			"filter_receiver": true,
			"receivers": [ 
				"you+data@yourprovider.com",
				"you+reports@yourprovider.com"
			],
			"subject": [ "DATA" ],
			"add_date": true,
			"destination": "/media/disk/data/"
        },
		{
			"filter_sender": false,
			"senders": [],
			"filter_receiver": false,
			"receivers": [],
			"subject": [ "BACKUP" ],
			"add_date": true,
			"destination": "/media/disk/backup/"
        }
    ],
    "use_gmail_trash_flag_with_delete": true,
    "filter_unread_emails": false,
    "mark_as_read": false,
    "delete_email": true,
    "mark_as_read_no_attachments": false,
    "delete_email_no_attachments": false,
    "mark_as_read_no_match": false,
    "delete_email_no_match": false
}
```

#### Behavior Configuration -- Mappings ####

There are three possible filters for each mapping: senders, receivers, and subject. These filters use the `filter_sender`, `senders`, `filter_receiver`, `receivers`, and `subject` properties.

When an email matches a mapping filter, the attachments will be saved according to the `add_date` and `subject` properties.

The following properties are needed:
 * `filter_sender`, specifying if the filter on sender's email address is active/considered or not
 * `senders`, specifying the list of allowed sender addresses (case-insensitive)
 * `filter_receiver`, specifying if the filter on the receiver's email address is active/considered or not
 * `receivers`, specifying the list of allowed receiver addresses (case-insensitive)
 * `subject`, specifying the text that must appear somewhere in the subject
 * `add_date`, specifying if the email date (in `YYYYMMDD` format) should be appended to the begin of the filename or not (if enabled, output format is in `20160731_attachment.ext` format)
 * `destination`, specifying the destination directory of attached files

#### Behavior Configuration -- General ####

The following are general settings for email management.

 * `use_gmail_trash_flag_with_delete` causes the gmail specifi trash flag to be used which is required to delete emails instead of archiving.
 * `filter_unread_emails` specifies if the program should only consider unread emails
 * `mark_as_read` specifies if the program should mark an email as read after its attachments are stored/archived
 * `delete_email` specifies if the program should delete an email as read after its attachments are stored/archived
 * `mark_as_read_no_attachments` specifies if the program should mark as read emails without attachments
 * `delete_email_no_attachments` specifies if the program should delete emails without attachments
 * `mark_as_read_no_match` specifies if the program should mark as read emails not matching the configured rules
 * `delete_email_no_match` specifies if the program should delete emails not matching the configured rules

### Notes ###

This program is an extended and customized version of a [code snipped found on Stack Overflow](http://stackoverflow.com/questions/10182499/how-do-i-download-only-unread-attachments-from-a-specific-gmail-label).
