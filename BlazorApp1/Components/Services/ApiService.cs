using System.Net.Http.Headers;
using System.Net.Http.Json;

namespace Altin_Fiyat_Takip_Analizi.Web.Services;

public class ApiService
{
    private readonly HttpClient _http;
    private readonly AuthTokenStore _tokenStore;

    public event Action? AuthStateChanged;

    public string? CurrentUsername => _tokenStore.Username;
    public string? CurrentRole    => _tokenStore.Role;

    public ApiService(HttpClient http, AuthTokenStore tokenStore)
    {
        _http = http;
        _tokenStore = tokenStore;

        // Store değiştiğinde Authorization header'ı senkronize tut
        _tokenStore.TokenChanged += SyncAuthHeader;
        SyncAuthHeader();
    }

    private void SyncAuthHeader()
    {
        if (!string.IsNullOrEmpty(_tokenStore.Token))
            _http.DefaultRequestHeaders.Authorization =
                new AuthenticationHeaderValue("Bearer", _tokenStore.Token);
        else
            _http.DefaultRequestHeaders.Authorization = null;

        AuthStateChanged?.Invoke();
    }

    public bool IsAuthenticated => _tokenStore.IsAuthenticated;

    public void SetToken(string token)
    {
        _tokenStore.Token = token;
        // SyncAuthHeader tokenChanged olayı üzerinden çağrılır
    }

    public void SetCurrentUser(string username, string role)
    {
        _tokenStore.Username = username;
        _tokenStore.Role     = role;
        AuthStateChanged?.Invoke();
    }

    public void ClearToken()
    {
        _tokenStore.Clear();
    }

    public async Task<T?> GetAsync<T>(string endpoint)
    {
        var response = await _http.GetAsync(endpoint);
        if (!response.IsSuccessStatusCode) return default;
        return await response.Content.ReadFromJsonAsync<T>();
    }

    public async Task<TResponse?> PostAsync<TRequest, TResponse>(string endpoint, TRequest body)
    {
        var response = await _http.PostAsJsonAsync(endpoint, body);
        if (!response.IsSuccessStatusCode) return default;
        return await response.Content.ReadFromJsonAsync<TResponse>();
    }

    public async Task<bool> PutAsync<TRequest>(string endpoint, TRequest body)
    {
        var response = await _http.PutAsJsonAsync(endpoint, body);
        return response.IsSuccessStatusCode;
    }

    public async Task<bool> DeleteAsync(string endpoint)
    {
        var response = await _http.DeleteAsync(endpoint);
        return response.IsSuccessStatusCode;
    }

    public async Task<TResponse?> PostEmptyAsync<TResponse>(string endpoint)
    {
        var response = await _http.PostAsync(endpoint, null);
        if (!response.IsSuccessStatusCode) return default;
        return await response.Content.ReadFromJsonAsync<TResponse>();
    }
}