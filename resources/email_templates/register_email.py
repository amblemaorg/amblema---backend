from flask import current_app


def messageRegisterEmail(email, password):
    return """
<!DOCTYPE html>
<html>

<head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title></title>
    <link href="https://fonts.googleapis.com/css?family=Montserrat:400,700&display=swap" rel="stylesheet">
</head>


<body>
    <center>
        <div style="margin:0;padding:0">
            <table width="100%" border="0" bgcolor="white" cellpadding="0" cellspacing="0" style="font-family:'Montserrat',font-size:12px;">
                <tbody>
                    <tr>
                        <td></td>
                        <td align="center">

                            <table border="0" bgcolor="white" cellpadding="0" cellspacing="0" style="max-width:780px;width:100%;">
                                <tbody>
                                    <tr>
                                        <td style="padding:10px 0 10px 0; text-align: center;">
                                            
                                            <table border="0" cellpadding="0" cellspacing="0" width="100%" bgcolor="transparent">
                                                <tbody>
                                                    <tr>
                                                        <td style="padding:5px 5px 0px 5px">
                                                            <h3 style="margin:30px 0 20px 0;font-size:30px;color:#008096;font-weight:bold;">¡Bienvenido a AmbLeMa!</h3>
                                                            <p style="margin:0px 10px 15px 10px;color: #008096;font-weight:bold;line-height:22px;text-align:center;">
                                                                Estamos emocionados de que hayas decidido formar parte de Fundación AmbLeMa.
                                                                Inicia la experiencia de ser parte de AmbLeMa completando algunos pasos.
                                                                Para ello ingresa a nuestra página con las siguientes credenciales:</p>
                                                            <p style="margin:0 0 0 0;color: #008096;line-height:22px;font-size: 18px;font-weight:bold">Usuario: """+email+"""</p>
                                                            <p style="margin:0 0 0 0;color: #008096;line-height:22px;font-size: 18px;font-weight:bold">Contraseña: """+password+"""</p>
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

                    <tr>
                        <td></td>
                        <td align="center">

                            <table border="0" bgcolor="white" cellpadding="0" cellspacing="0" style="max-width:780px;width:100%;">
                                <tbody>
                                    <tr>
                                        <td align="center" style="padding:10px 0 10px 0; text-align: center;">
                                            
                                            <table border="0" cellpadding="0" cellspacing="0" width="100%" bgcolor="transparent">
                                                <tbody>
                                                    <tr>
                                                        <td></td>

                                                        <td align="center" style="padding:5px 1px 5px 1px">
                                                            <table border="0" cellpadding="0" cellspacing="0" width="100%" bgcolor="transparent" style="max-width: 500px; background-position: center;
      background-repeat: no-repeat;
      background-size: 90% 100%;
      background-image: url("""+current_app.config.get('SERVER_URL')+"""/resources/images/mailing/register-background.png);">
                                                                <tbody>
                                                                    <tr>
                                                                        <td align="center">
                                                                            <br>
                                                                            <p style="padding: 70px 85px 0px 85px;color: #00353A;font-weight:bold;line-height:22px">
                                                                                Si quieres contactar con nuestro equipo, no dudes en hacerlo a través de info@amblema.org
                                                                            </p>
                                                                            <p style="margin:20px 10px 0px 10px;color: #00353A;font-weight:bold;line-height:20px">Ten un excelente día</p>
                                                                            <p style="margin:0px 10px 20px 10px;color: #00353A;font-weight:bold;line-height:20px">Fundación AmbLeMa</p> 
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
  Inicia la experiencia de ser parte de AmbLeMa completando algunos pasos.
  Para ello ingresa a nuestra página con las siguientes credenciales:

  Usuario: """+email+"""
  Contraseña: """+password+"""

  Si quieres contactar con nuestro equipo, no dudes en hacerlo a través de info@amblema.org

  Ten un excelente día
  Fundación AmbLeMa
  """
