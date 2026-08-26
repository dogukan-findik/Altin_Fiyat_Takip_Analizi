namespace Altin_Fiyat_Takip_Analizi.Web.Services;

/// <summary>
/// Singleton olarak kaydedilen bu servis, JWT token'ını belleğin dışına taşımadan
/// Blazor Server circuit'leri arasında paylaşır.
/// Her kullanıcı aynı sunucuya bağlı olduğundan (Blazor Server), tek bir token yeterlidir.
/// </summary>
public class AuthTokenStore
{
    private string? _token;
    private string? _username;
    private string? _role;

    public event Action? TokenChanged;

    public string? Token
    {
        get => _token;
        set
        {
            _token = value;
            TokenChanged?.Invoke();
        }
    }

    public string? Username
    {
        get => _username;
        set { _username = value; TokenChanged?.Invoke(); }
    }

    public string? Role
    {
        get => _role;
        set { _role = value; TokenChanged?.Invoke(); }
    }

    public bool IsAuthenticated => !string.IsNullOrEmpty(_token);

    public void Clear()
    {
        _token = null;
        _username = null;
        _role = null;
        TokenChanged?.Invoke();
    }
}
