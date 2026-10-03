from flask import current_app


def messageRegisterEmail(email, password):
    return """
<!DOCTYPE html>
<html>

<head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Bienvenido a AmbLeMa</title>
    <link href="https://fonts.googleapis.com/css?family=Montserrat:400,700&display=swap" rel="stylesheet">
    <style type="text/css">
        body, table, td, a { -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; }
        table, td { mso-table-lspace: 0pt; mso-table-rspace: 0pt; }
        img { -ms-interpolation-mode: bicubic; border: 0; outline: none; text-decoration: none; }

        /* Forzar underline en enlace Sistema PECA para clientes moviles y web */
        a.link-peca, a.link-peca:link, a.link-peca:visited, a.link-peca strong {
            color: #00809A !important;
            text-decoration: underline !important;
        }

        /* Hover para el botón */
        .btn-peca:hover {
            background-color: #6ea232 !important;
            border-color: #6ea232 !important;
        }

        /* Responsive movil */
        @media only screen and (max-width: 600px) {
            .mobile-table {
                width: 100% !important;
            }
            .mobile-title {
                font-size: 24px !important;
                margin: 20px 0 15px 0 !important;
            }
            .mobile-text {
                font-size: 14px !important;
                line-height: 20px !important;
            }
            .mobile-btn-table {
                width: 100% !important;
                max-width: 280px !important;
            }
            .btn-peca {
                display: block !important;
                padding: 12px 16px !important;
                border-left-width: 10px !important;
                border-right-width: 10px !important;
                font-size: 15px !important;
            }
            .footer-bg {
                background-size: 100% 100% !important;
            }
            .footer-text {
                padding: 50px 20px 0px 20px !important;
                font-size: 13px !important;
            }
        }
    </style>
</head>


<body>
    <center>
        <div style="margin:0;padding:0">
            <table width="100%" border="0" bgcolor="white" cellpadding="0" cellspacing="0" style="font-family:'Montserrat', Arial, sans-serif;font-size:12px;">
                <tbody>
                    <tr>
                        <td></td>
                        <td align="center">

                            <table border="0" bgcolor="white" cellpadding="0" cellspacing="0" class="mobile-table" style="max-width:780px;width:100%;">
                                <tbody>
                                    <tr>
                                        <td style="padding:10px 0 10px 0; text-align: center;">
                                            
                                            <table border="0" cellpadding="0" cellspacing="0" width="100%" bgcolor="transparent">
                                                <tbody>
                                                    <tr>
                                                        <td style="padding:5px 5px 0px 5px">
                                                            <h3 class="mobile-title" style="margin:30px 0 20px 0;font-size:30px;color:#008096;font-weight:bold;">¡Bienvenido a AmbLeMa!</h3>
                                                            <p class="mobile-text" style="margin:0px 10px 15px 10px;color: #008096;font-weight:bold;line-height:22px;text-align:center;">
                                                                Estamos emocionados de que hayas decidido formar parte de Fundación AmbLeMa.<br/>
                                                                Para <strong>continuar tu proceso</strong>, ingresa al <a href="https://amblema.org/auth/login" target="_blank" class="link-peca" style="color: #00809A; text-decoration: underline;"><strong style="color: #00809A; text-decoration: underline;">Sistema PECA</strong></a> y completa cada uno de los pasos necesarios para <strong>finalizar tu registro</strong>.<br/>
                                                                Accede con las siguientes credenciales:
                                                            </p>
                                                            <p style="margin:0 0 6px 0;color: #008096;line-height:22px;font-size: 18px;font-weight:bold">Usuario: """+email+"""</p>
                                                            <p style="margin:0 0 0 0;color: #008096;line-height:22px;font-size: 18px;font-weight:bold">Contraseña: """+password+"""</p>

                                                            <!-- Botón Ir al Sistema PECA (Verde Amblema) -->
                                                            <table border="0" cellpadding="0" cellspacing="0" align="center" class="mobile-btn-table" style="margin: 25px auto 15px auto;">
                                                                <tbody>
                                                                    <tr>
                                                                        <td align="center" bgcolor="#81B03E" style="border-radius: 6px; background-color: #81B03E;">
                                                                            <a href="https://amblema.org/auth/login" target="_blank" class="btn-peca" style="background-color: #81B03E; border: 12px solid #81B03E; border-left: 28px solid #81B03E; border-right: 28px solid #81B03E; border-radius: 6px; font-family: 'Montserrat', Arial, sans-serif; font-size: 15px; font-weight: bold; color: #ffffff; text-decoration: none; display: inline-block; text-align: center; mso-padding-alt: 0;">
                                                                                Ir al Sistema PECA
                                                                            </a>
                                                                        </td>
                                                                    </tr>
                                                                </tbody>
                                                            </table>

                                                        </td>
                                                    </tr>
                                                </tbody>
                                            </table>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </td>
                        <td></td>
                    </tr>

                    <tr>
                        <td></td>
                        <td align="center">

                            <table border="0" bgcolor="white" cellpadding="0" cellspacing="0" class="mobile-table" style="max-width:780px;width:100%;">
                                <tbody>
                                    <tr>
                                        <td align="center" style="padding:10px 0 10px 0; text-align: center;">
                                            
                                            <table border="0" cellpadding="0" cellspacing="0" width="100%" bgcolor="transparent">
                                                <tbody>
                                                    <tr>
                                                        <td></td>

                                                        <td align="center" style="padding:5px 1px 5px 1px">
                                                            <table border="0" cellpadding="0" cellspacing="0" width="100%" bgcolor="transparent" class="footer-bg" style="max-width: 500px; background-position: center;
      background-repeat: no-repeat;
      background-size: 90% 100%;
      background-image: url("""+current_app.config.get('SERVER_URL')+"""/resources/images/mailing/register-background.png);">
                                                                <tbody>
                                                                    <tr>
                                                                        <td align="center">
                                                                            <br>
                                                                            <p class="footer-text" style="padding: 70px 85px 0px 85px;color: #00353A;font-weight:bold;line-height:22px">
                                                                                Si necesitas apoyo, puedes escribirnos a amblemaorg@gmail.com
                                                                            </p>
                                                                            <p style="margin:20px 10px 0px 10px;color: #00353A;font-weight:bold;line-height:20px">Fundación AmbLeMa</p>
                                                                            <p style="margin:0px 10px 20px 10px;color: #00353A;font-weight:bold;line-height:20px">Teléfono de contacto: 0414-1000456</p> 
                                                                            <br>
                                                                            <br>
                                                                            <br>
                                                                            <br>
                                                                            <br>
                                                                            <br>
                                                                        </td>
                                                                    </tr>
                                                                </tbody>
                                                            </table>
                                                            
                                                        </td>
                                                        <td></td>
                                                    </tr>
                                                </tbody>
                                            </table>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>

                        </td>
                        <td></td>
                    </tr>
                </tbody>
            </table>
        </div>
    </center>
</body>
</html>
"""


def messageRegisterEmailPlainText(email, password):
    return """
  Amblema - Registro de usuario

  ¡Bienvenido a AmbLeMa!

  Estamos emocionados de que hayas decidido formar parte de Fundación AmbLeMa.
  Para continuar tu proceso, ingresa al Sistema PECA y completa cada uno de los pasos necesarios para finalizar tu registro.
  Accede con las siguientes credenciales:

  Usuario: """+email+"""
  Contraseña: """+password+"""

  Ir al Sistema PECA: https://amblema.org/auth/login

  Si necesitas apoyo, puedes escribirnos a amblemaorg@gmail.com

  Fundación AmbLeMa
  Teléfono de contacto: 0414-1000456
  """
