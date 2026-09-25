function doGet(e) {
  return ContentService.createTextOutput(exportarEEncriptarCSV())
}

function exportarEEncriptarCSV() {

  console.log('secret_crypto e iv_crypto devem ser configurados nas propriedades do script (Project Properties)')

  const pg_dados = 'Registros'

  const props = PropertiesService.getScriptProperties()

  const secret_crypto = props.getProperty('secret_crypto')
  const iv_crypto = props.getProperty('iv_crypto')

  eval(UrlFetchApp.fetch("https://cdnjs.cloudflare.com/ajax/libs/crypto-js/4.2.0/crypto-js.min.js").getContentText())

  var ss = SpreadsheetApp.getActiveSpreadsheet()
  var sheet = ss.getSheetByName(pg_dados);
  // Pega o fuso horário configurado na planilha (ex: GMT-03:00)
  var timeZone = ss.getSpreadsheetTimeZone();
  
  // Usa getValues() para manter os tipos originais (Texto, Número, Date)
  var data = sheet.getDataRange().getValues();
  
  // 1. Converter os dados para formato CSV formatando datas e aspas
  var csvContent = data.map(function(row) {
    return row.map(function(cell) {
      var text;
      
      // Se a célula for um objeto do tipo Data, formata como dd/MM/yyyy
      if (cell instanceof Date) {
        text = Utilities.formatDate(cell, timeZone, "dd/MM/yyyy");
      } else {
        text = cell.toString().replace(/"/g, '""');
      }
      
      return '"' + text + '"';
    }).join(",");
  }).join("\n");

  // 2. Definir a Chave e o IV (Vetor de Inicialização)
  // IMPORTANTE: A chave deve ter 32 caracteres (256 bits) e o IV 16 caracteres (128 bits)
  var SECRET_KEY = CryptoJS.enc.Utf8.parse(secret_crypto); // 32 bytes
  var SECRET_IV  = CryptoJS.enc.Utf8.parse(iv_crypto);                 // 16 bytes

  // 3. Criptografar a string CSV com AES-256-CBC
  var encrypted = CryptoJS.AES.encrypt(csvContent, SECRET_KEY, {
    iv: SECRET_IV,
    mode: CryptoJS.mode.CBC,
    padding: CryptoJS.pad.Pkcs7
  });

  // O resultado criptografado em Base64
  return encrypted.toString();
}