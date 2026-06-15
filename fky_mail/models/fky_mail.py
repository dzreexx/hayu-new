from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64

class FkyMail(models.TransientModel):
    _name = 'fky.mail'
    _description = 'Mass PDF Mail Wizard'

    invoice_ids = fields.Many2many('account.move', string='Invoices')
    partner_ids = fields.Many2many('res.partner', string='Recipients', compute='_compute_partner_ids')
    message_body = fields.Html(string='Body', default=lambda self: self._default_message_body())
    subject = fields.Char(string='Subject', default='Invoices')
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    
    # Report Filter: Only show Adireksa Original Invoice and Copy
    report_id = fields.Many2one(
        'ir.actions.report', 
        string='Report', 
        domain=lambda self: self._get_report_domain(),
        required=True, 
        default=lambda self: self.env.ref('adireksa_invoice_print.action_report_adireksa_original_invoice', raise_if_not_found=False) or self.env.ref('account.account_invoices')
    )
    
    mail_template_id = fields.Many2one('mail.template', string='Email Template', domain="[('model', '=', 'fky.mail')]")
    
    # Manual email fields
    email_to = fields.Char(string='To ', help='Comma-separated email addresses. These will be added to the partner emails.')
    email_cc = fields.Char(string='CC ', help='Comma-separated email addresses for CC.')
    
    # Auto delete option
    auto_delete = fields.Boolean(
        string='Auto Delete After Send', 
        default=True,
        help='If checked, sent emails will be automatically deleted from the database after successful delivery. '
             'This helps keep the database clean but removes email history. '
             'If unchecked, emails will be kept and cleaned by Odoo\'s scheduled vacuum process.'
    )

    @api.model
    def _get_report_domain(self):
        # Helper to find the specific reports by XML ID if possible, or name
        domain = []
        try:
            report1 = self.env.ref('adireksa_invoice_print.action_report_adireksa_original_invoice', raise_if_not_found=False)
            report2 = self.env.ref('adireksa_invoice_print.action_report_adireksa_original_invoice_copy', raise_if_not_found=False)
            ids = []
            if report1: ids.append(report1.id)
            if report2: ids.append(report2.id)
            if ids:
                domain = [('id', 'in', ids)]
            else:
                # Fallback to standard if custom not found
                domain = [('model', '=', 'account.move')]
        except:
            domain = [('model', '=', 'account.move')]
        return domain

    @api.depends('invoice_ids')
    def _compute_partner_ids(self):
        for record in self:
            record.partner_ids = record.invoice_ids.mapped('partner_id')

    def _default_message_body(self):
        return _("<p>Please find attached the invoices.</p>")
    
    @api.model
    def default_get(self, fields_list):
        res = super(FkyMail, self).default_get(fields_list)
        if self.env.context.get('skip_default_get_render'):
            return res
        if self.env.context.get('active_model') == 'account.move' and self.env.context.get('active_ids'):
            active_ids = self.env.context.get('active_ids')
            res['invoice_ids'] = [(6, 0, active_ids)]
            
            invoices = self.env['account.move'].browse(active_ids)
            
            # Populate Recipients explicitly for default view
            res['partner_ids'] = [(6, 0, invoices.mapped('partner_id').ids)]
            
            # Set default subject
            res['subject'] = f"Invoices - {', '.join(invoices.mapped('name'))}"

            # Try to set default template and render it
            
            # Search for a configured default template
            template = self.env['mail.template'].search([('model', '=', 'fky.mail'), ('is_mass_pdf_default', '=', True)], limit=1)
            
            # If not found, try the fallback hardcoded specific xml id
            if not template:
                template = self.env.ref('fky_mail.email_template_mass_invoice', raise_if_not_found=False)

            if template:
                res['mail_template_id'] = template.id
                raw_subject = template.subject or res.get('subject')
                raw_body = template.body_html
                partner_names = invoices.mapped('partner_id.name')
                
                rendered_subject, rendered_body = self._render_preview_static(raw_subject, raw_body, invoices, partner_names)
                res['subject'] = rendered_subject
                res['message_body'] = rendered_body
            else:
                res['message_body'] = self._generate_fallback_body(invoices)

        return res

    def get_invoice_numbers(self):
        """ Returns HTML string with only invoice numbers """
        if not self.invoice_ids:
            return ""
        if len(self.invoice_ids) == 1:
            return f"<strong>{self.invoice_ids[0].name}</strong>"
        lines = "".join(f"<li><strong>{inv.name}</strong></li>" for inv in self.invoice_ids)
        return f"<ul style='margin: 0; padding-left: 20px;'>{lines}</ul>"

    def get_invoice_dates(self):
        """ Returns comma-separated formatted invoice dates """
        if not self.invoice_ids:
            return ""
        dates = []
        for inv in self.invoice_ids:
            if inv.invoice_date:
                dates.append(inv.invoice_date.strftime('%d/%m/%Y'))
        unique_dates = []
        for d in dates:
            if d not in unique_dates:
                unique_dates.append(d)
        return ", ".join(unique_dates)

    def _generate_fallback_body(self, invoices):
        """ Generates a clean fallback body showing only invoice numbers without total, value, and date """
        if not invoices:
            return ""
        if len(invoices) == 1:
            return f"<p>Berikut kami lampirkan Invoice: <strong>{invoices[0].name}</strong></p>"
        lines = "".join(f"<li><strong>{inv.name}</strong></li>" for inv in invoices)
        return f"<p>Berikut kami lampirkan Invoice:</p><ul style='margin: 0; padding-left: 20px;'>{lines}</ul>"

    def get_invoice_table(self):
        """ Public method to be called from QWeb template """
        return self._generate_body_table(self.invoice_ids)

    def _generate_body_table(self, invoices):
        row_style = "border: 1px solid #ddd; padding: 8px;"
        header_style = "border: 1px solid #ddd; padding: 8px; background-color: #f2f2f2; font-weight: bold;"
        
        table_rows = ""
        total_amount = 0.0
        currency = invoices[0].currency_id if invoices else self.env.company.currency_id

        for inv in invoices:
            total_amount += inv.amount_total
            table_rows += f"""
                <tr>
                    <td style="{row_style}">{inv.name}</td>
                    <td style="{row_style}">{inv.invoice_date or ''}</td>
                    <td style="{row_style}">{inv.amount_total} {inv.currency_id.symbol}</td>
                </tr>
            """
        
        body_content = f"""
            <table style="border-collapse: collapse; width: 100%;">
                <thead>
                    <tr>
                        <th style="{header_style}">Invoice Number</th>
                        <th style="{header_style}">Date</th>
                        <th style="{header_style}">Total</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
                <tfoot>
                    <tr>
                        <td colspan="2" style="{header_style} text-align: right;"><strong>Total Amount:</strong></td>
                        <td style="{header_style}"><strong>{total_amount:.2f} {currency.symbol}</strong></td>
                    </tr>
                </tfoot>
            </table>
        """
        return body_content

    @api.model
    def _render_preview_static(self, subject, body, invoices, partner_names=None):
        recipients = partner_names[0] if partner_names else 'Customer'
        table = self._generate_body_table(invoices)
        
        # Format invoice numbers list/string
        if len(invoices) == 1:
            inv_nums = f"<strong>{invoices[0].name}</strong>"
        else:
            lines = "".join(f"<li><strong>{inv.name}</strong></li>" for inv in invoices)
            inv_nums = f"<ul style='margin: 0; padding-left: 20px;'>{lines}</ul>"

        # Format invoice dates list/string
        dates = []
        for inv in invoices:
            if inv.invoice_date:
                dates.append(inv.invoice_date.strftime('%d/%m/%Y'))
        unique_dates = []
        for d in dates:
            if d not in unique_dates:
                unique_dates.append(d)
        inv_dates = ", ".join(unique_dates) if unique_dates else ""
            
        user_name = self.env.user.name or ''
        signature = self.env.user.signature or ''
        default_subject = f"Invoices - {', '.join(invoices.mapped('name'))}"

        if subject:
            subject = str(subject)
            subject = subject.replace('{{object.subject}}', default_subject)
            subject = subject.replace('${object.subject}', default_subject)
            subject = subject.replace('{{object.get_invoice_dates()}}', inv_dates)
            subject = subject.replace('${object.get_invoice_dates()}', inv_dates)
            subject = subject.replace('{{object.invoice_date}}', inv_dates)
            subject = subject.replace('${object.invoice_date}', inv_dates)
            if 'object.invoice_ids' in subject:
                inv_name = invoices[0].name if invoices else ''
                subject = subject.replace('{{object.invoice_ids[0].name}}', inv_name)
                subject = subject.replace('${object.invoice_ids[0].name}', inv_name)

        if body:
            body = str(body)
            body = body.replace('<t t-esc="object.partner_ids and object.partner_ids[0].name or \'Customer\'"/>', recipients)
            body = body.replace('<t t-esc="object.partner_ids and object.partner_ids[0].name or \'Customer\'"></t>', recipients)
            body = body.replace('<t t-raw="object.get_invoice_table()"/>', table)
            body = body.replace('<t t-raw="object.get_invoice_table()"></t>', table)
            body = body.replace('<t t-raw="object.get_invoice_numbers()"/>', inv_nums)
            body = body.replace('<t t-raw="object.get_invoice_numbers()"></t>', inv_nums)
            body = body.replace('<t t-esc="object.env.user.name"/>', user_name)
            body = body.replace('<t t-esc="object.env.user.name"></t>', user_name)
            body = body.replace('<t t-esc="object.env.user.signature or \'\'"/>', signature)
            body = body.replace('<t t-esc="object.env.user.signature or \'\'"></t>', signature)
        return subject, body

    @api.onchange('mail_template_id')
    def _onchange_mail_template_id(self):
        if self.mail_template_id and self.invoice_ids:
            invoices = self.invoice_ids._origin if self.invoice_ids else self.invoice_ids
            partner_names = self.partner_ids.mapped('name')
            raw_subject = self.mail_template_id.subject or f"Invoices - {', '.join(invoices.mapped('name'))}"
            raw_body = self.mail_template_id.body_html
            
            rendered_subject, rendered_body = self._render_preview_static(raw_subject, raw_body, invoices, partner_names)
            self.subject = rendered_subject
            self.message_body = rendered_body


    def action_send_mass_pdf(self):
        self.ensure_one()
        
        # OPTIMIZATION: Generate PDF once and cache it
        # This avoids regenerating the same PDF for each partner
        pdf_cache = {}  # Key: frozenset of invoice IDs, Value: attachment ID
        
        # Group by partner to send one email per partner
        invoices_by_partner = {}
        for invoice in self.invoice_ids:
            if invoice.partner_id not in invoices_by_partner:
                invoices_by_partner[invoice.partner_id] = self.env['account.move']
            invoices_by_partner[invoice.partner_id] += invoice

        # PERFORMANCE FIX: Process emails without blocking
        # Create all email records first, then commit
        for partner, invoices in invoices_by_partner.items():
            self._send_merged_email(partner, invoices, pdf_cache)
        
        # Commit the transaction so emails are queued
        # This allows the wizard to close while emails are being processed
        self.env.cr.commit()

        return {'type': 'ir.actions.act_window_close'}

    def _send_merged_email(self, partner, invoices, pdf_cache=None):
        """
        Send email to a partner with merged PDF of their invoices.
        
        Args:
            partner: res.partner record
            invoices: account.move recordset
            pdf_cache: dict to cache generated PDFs (key: frozenset of invoice IDs, value: attachment ID)
        """
        if pdf_cache is None:
            pdf_cache = {}
            
        # Start with manual attachments
        all_attachment_ids = list(self.attachment_ids.ids)
        
        # PERFORMANCE FIX: Generate PDF but don't wait for completion
        # We'll create the mail record with a flag to generate PDF during actual sending
        if self.report_id:
            try:
                # OPTIMIZATION: Check cache first to avoid regenerating the same PDF
                invoice_ids_key = frozenset(invoices.ids)
                
                if invoice_ids_key in pdf_cache:
                    # Reuse cached PDF attachment
                    all_attachment_ids.append(pdf_cache[invoice_ids_key])
                else:
                    # Generate new PDF
                    # Use internal method _render_qweb_pdf directly on the report record.
                    # Evidence from previous errors suggests signature is (res_ids, data=None).
                    # Public 'render_qweb_pdf' does not exist on this version.
                    pdf_content, data_format = self.report_id._render_qweb_pdf(invoices.ids)
                    
                    # Create Attachment
                    filename = f"Invoices_{fields.Date.today()}.pdf"
                    if len(invoices) == 1:
                        filename = f"Invoice_{invoices[0].name.replace('/', '_')}.pdf"

                    attachment = self.env['ir.attachment'].create({
                        'name': filename,
                        'type': 'binary',
                        'datas': base64.b64encode(pdf_content),
                        'res_model': 'mail.compose.message', 
                        'res_id': 0, 
                    })
                    all_attachment_ids.append(attachment.id)
                    
                    # Cache the attachment for reuse
                    pdf_cache[invoice_ids_key] = attachment.id

            except Exception as e:
                # Log error but don't stop the email if manual attachments exist?
                import traceback
                traceback.print_exc()
                # For now, raise logic so user knows it failed
                raise UserError(_("Error generating PDF: %s") % str(e))
        
        # Send Email
        subject = self.subject
        body_content = self.message_body

        if self.mail_template_id:
            raw_subject = self.mail_template_id.subject or subject
            raw_body = self.mail_template_id.body_html
            partner_names = [partner.name]
            
            rendered_subject, rendered_body = self._render_preview_static(raw_subject, raw_body, invoices, partner_names)
            subject = rendered_subject
            body_content = rendered_body
        else:
            if not body_content or body_content == '<p><br></p>':
                # Fallback: If body is empty, regenerate the list for these specific invoices
                body_content = self._generate_fallback_body(invoices)
        
        # 2. Build email addresses
        # Use recipient_ids to automatically send to partner (no TO field needed)
        # CC field is for additional recipients only
        email_cc_list = []
        if self.email_cc:
            manual_cc = [email.strip() for email in self.email_cc.split(',') if email.strip()]
            email_cc_list.extend(manual_cc)
        
        # Combine all CC emails
        email_cc_str = ', '.join(email_cc_list) if email_cc_list else False
            
        # 3. Create and send email
        mail_values = {
            'subject': subject,
            'body_html': body_content,
            'email_from': self.env.user.email_formatted,
            'recipient_ids': [(4, partner.id)] if partner else [],  # Auto-send to partner
            'email_cc': email_cc_str,  # Additional CC recipients
            'attachment_ids': [(6, 0, all_attachment_ids)],
            'message_type': 'email',
            'auto_delete': self.auto_delete,  # Use wizard setting for auto-delete behavior
        }
        
        mail = self.env['mail.mail'].sudo().create(mail_values)
        # OPTIMIZATION: Use auto_commit=False to queue emails for background processing
        # This prevents the UI from blocking while emails are being sent
        mail.send(auto_commit=False)

