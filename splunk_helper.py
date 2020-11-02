import re


def find_attribute_from_tag(text):
    try:
        result = [x.group() for x in re.finditer(fr'([^ ]*="[^"]*")', text)]
        output = {}
        output.update({'Request' if text[1:8] == 'Request' else 'Response':
                           {result[i].split('"')[0]: result[i].split('"')[1] for i in range(len(result))}})
        return output
    except Exception as e:
        raise Exception(f"Exception occured with message: {e}")


if __name__ == '__main__':
    res = find_attribute_from_tag('MerchantId', '''<Request><Header MessageType="60" SerialNumber="100120107760" Username="DealerAKaynar3" Password="********" ParameterVersion="0" BatchNo="248" TraceNo="174" TerminalId="10009116" MerchantId="S380500" LanguageCode="tr-TR" OperationSource="23" SecondarySerialNumber="JI20107760" BankMerchantCodes="062:1168748" TerminalDateTime="201026173847"></Header><Body CustomerCode="5377628926" ><Banks><Bank Id="062" BankAppVer="00D95897" MerchantCode="1168748" /></Banks></Body></Request>', 'ResponseMessage': '<Response><Header ResponseCode="X_VFTR_EKOS_40" Status="3" Message="X_VFTR_EKOS_40 - Sistemde geçici bir problem oluştu. Lütfen daha sonra tekrar deneyiniz." HostDateTime="201026173920"/><Body></Body></Response>''')
    print(res)