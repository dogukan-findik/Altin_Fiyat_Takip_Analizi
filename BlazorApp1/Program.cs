using Altin_Fiyat_Takip_Analizi.Web.Components;
using Altin_Fiyat_Takip_Analizi.Web.Services;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddHttpClient("AltinFiyatApiClient", client =>
{
    client.BaseAddress = new Uri("https://localhost:7268/");
});

// Token'ı circuit'ler arasında yaşatmak için Singleton
builder.Services.AddSingleton<AuthTokenStore>();

builder.Services.AddScoped<ApiService>(sp =>
{
    var factory    = sp.GetRequiredService<IHttpClientFactory>();
    var httpClient = factory.CreateClient("AltinFiyatApiClient");
    var tokenStore = sp.GetRequiredService<AuthTokenStore>();
    return new ApiService(httpClient, tokenStore);
});

// Add services to the container.
builder.Services.AddRazorComponents()
    .AddInteractiveServerComponents();

var app = builder.Build();

// Configure the HTTP request pipeline.
if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Error", createScopeForErrors: true);
    // The default HSTS value is 30 days. You may want to change this for production scenarios, see https://aka.ms/aspnetcore-hsts.
    app.UseHsts();
}

app.UseHttpsRedirection();

app.UseStaticFiles();
app.UseAntiforgery();

app.MapRazorComponents<App>()
    .AddInteractiveServerRenderMode();

app.Run();
